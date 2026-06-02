"""Локальный HTTP-прокси для Cursor: 127.0.0.1 -> пул upstream с failover.

Cursor один раз указывает http://127.0.0.1:PORT — relay сам переключает живой IP.
"""

from __future__ import annotations

import base64
import logging
import select
import socket
import threading
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse

from config import normalize_proxy_url
from proxy_probe import mask_proxy_endpoint, probe_proxy_tcp

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UpstreamProxy:
    label: str
    url: str
    host: str
    port: int
    auth_header: str | None

    @property
    def endpoint(self) -> str:
        return mask_proxy_endpoint(self.url)


def parse_upstream_pool(raw_urls: list[str]) -> list[UpstreamProxy]:
    out: list[UpstreamProxy] = []
    seen: set[str] = set()
    for i, raw in enumerate(raw_urls):
        raw = (raw or "").strip()
        if not raw:
            continue
        norm = normalize_proxy_url(raw)
        key = mask_proxy_endpoint(norm)
        if key in seen:
            continue
        seen.add(key)
        parsed = urlparse(norm)
        host = parsed.hostname or ""
        port = parsed.port or 8000
        auth_header = None
        if parsed.username and parsed.password:
            token = base64.b64encode(
                f"{parsed.username}:{parsed.password}".encode()
            ).decode("ascii")
            auth_header = f"Basic {token}"
        out.append(
            UpstreamProxy(
                label=f"pool_{i + 1}",
                url=norm,
                host=host,
                port=port,
                auth_header=auth_header,
            )
        )
    return out


def probe_pool(pool: list[UpstreamProxy], *, timeout: float = 6.0) -> list[bool]:
    return [probe_proxy_tcp(u.url, timeout=timeout)[0] for u in pool]


class CursorProxyRelay:
    def __init__(
        self,
        pool: list[UpstreamProxy],
        *,
        bind_host: str = "127.0.0.1",
        bind_port: int = 18777,
        probe_interval_sec: float = 45.0,
    ) -> None:
        if not pool:
            raise ValueError("upstream pool is empty")
        self._pool = pool
        self._bind_host = bind_host
        self._bind_port = bind_port
        self._probe_interval_sec = max(10.0, probe_interval_sec)
        self._lock = threading.Lock()
        self._index = 0
        self._alive: list[bool] = [True] * len(pool)
        self._stop = threading.Event()
        self._server: socket.socket | None = None

    @property
    def listen_addr(self) -> str:
        return f"http://{self._bind_host}:{self._bind_port}"

    def status_line(self) -> str:
        with self._lock:
            parts = []
            for i, u in enumerate(self._pool):
                mark = "OK" if self._alive[i] else "down"
                cur = " *" if i == self._index else ""
                parts.append(f"{u.endpoint}({mark}){cur}")
            return " | ".join(parts)

    def _refresh_alive(self) -> None:
        alive = probe_pool(self._pool)
        with self._lock:
            self._alive = alive
            if not alive[self._index]:
                for j, ok in enumerate(alive):
                    if ok:
                        self._index = j
                        logger.warning(
                            "relay: switch -> %s", self._pool[j].endpoint
                        )
                        break

    def _probe_loop(self) -> None:
        while not self._stop.wait(self._probe_interval_sec):
            try:
                self._refresh_alive()
                logger.info("relay probe: %s", self.status_line())
            except Exception as exc:
                logger.warning("relay probe error: %s", exc)

    def _next_upstream(self) -> UpstreamProxy | None:
        with self._lock:
            n = len(self._pool)
            for offset in range(n):
                idx = (self._index + offset) % n
                if self._alive[idx]:
                    self._index = idx
                    return self._pool[idx]
            return None

    def _mark_failed(self, upstream: UpstreamProxy) -> None:
        with self._lock:
            for i, u in enumerate(self._pool):
                if u.url == upstream.url:
                    self._alive[i] = False
                    break

    def _connect_upstream(
        self, upstream: UpstreamProxy, target_host: str, target_port: int
    ) -> socket.socket:
        up = socket.create_connection((upstream.host, upstream.port), timeout=12)
        lines = [
            f"CONNECT {target_host}:{target_port} HTTP/1.1",
            f"Host: {target_host}:{target_port}",
        ]
        if upstream.auth_header:
            lines.append(f"Proxy-Authorization: {upstream.auth_header}")
        lines.extend(["", ""])
        up.sendall("\r\n".join(lines).encode("latin-1"))
        buf = b""
        while b"\r\n\r\n" not in buf and len(buf) < 65536:
            chunk = up.recv(4096)
            if not chunk:
                up.close()
                raise OSError("upstream closed before CONNECT response")
            buf += chunk
        head = buf.split(b"\r\n\r\n", 1)[0].decode("latin-1", errors="replace")
        status_line = head.split("\r", 1)[0]
        if " 200 " not in status_line:
            up.close()
            raise OSError(f"upstream CONNECT failed: {status_line[:120]}")
        return up

    @staticmethod
    def _pipe(a: socket.socket, b: socket.socket) -> None:
        sockets = [a, b]
        try:
            while True:
                readable, _, errored = select.select(sockets, [], sockets, 120)
                if errored:
                    break
                if not readable:
                    break
                for s in readable:
                    data = s.recv(8192)
                    if not data:
                        return
                    dst = b if s is a else a
                    dst.sendall(data)
        finally:
            for s in sockets:
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    s.close()
                except OSError:
                    pass

    def _handle_client(self, client: socket.socket) -> None:
        try:
            client.settimeout(30)
            first = b""
            while b"\r\n" not in first and len(first) < 8192:
                chunk = client.recv(4096)
                if not chunk:
                    return
                first += chunk
            line = first.split(b"\r\n", 1)[0].decode("latin-1", errors="replace")
            parts = line.split()
            if len(parts) < 2 or parts[0].upper() not in ("CONNECT", "GET", "POST"):
                client.close()
                return
            method = parts[0].upper()
            if method == "CONNECT":
                host, _, port_s = parts[1].partition(":")
                port = int(port_s or "443")
            else:
                parsed = urlparse(parts[1])
                host = parsed.hostname or ""
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
            if not host:
                client.close()
                return

            tried = 0
            n = len(self._pool)
            while tried < n:
                upstream = self._next_upstream()
                if upstream is None:
                    break
                tried += 1
                try:
                    remote = self._connect_upstream(upstream, host, port)
                    if method == "CONNECT":
                        client.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                    self._pipe(client, remote)
                    return
                except OSError as exc:
                    logger.warning(
                        "relay %s -> %s:%s fail: %s",
                        upstream.endpoint,
                        host,
                        port,
                        exc,
                    )
                    self._mark_failed(upstream)
            client.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
        except Exception as exc:
            logger.debug("client handler: %s", exc)
        finally:
            try:
                client.close()
            except OSError:
                pass

    def serve_forever(self, *, on_listen: Callable[[], None] | None = None) -> None:
        self._refresh_alive()
        probe_t = threading.Thread(target=self._probe_loop, daemon=True)
        probe_t.start()
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((self._bind_host, self._bind_port))
        srv.listen(64)
        self._server = srv
        logger.info("relay listen %s pool=%d", self.listen_addr, len(self._pool))
        if on_listen:
            on_listen()
        try:
            while not self._stop.is_set():
                try:
                    srv.settimeout(1.0)
                    client, _addr = srv.accept()
                except TimeoutError:
                    continue
                threading.Thread(
                    target=self._handle_client,
                    args=(client,),
                    daemon=True,
                ).start()
        finally:
            srv.close()

    def stop(self) -> None:
        self._stop.set()
        if self._server:
            try:
                self._server.close()
            except OSError:
                pass
