"""TCP-проверка прокси перед Telethon (fail-closed, без подключения с домашнего IP)."""

from __future__ import annotations

import os
import socket
import time
from typing import Callable
from urllib.parse import urlparse

from config import normalize_proxy_url

_last_proxy_alert_at = 0.0
_last_proxy_alert_key = ""


class ProxyUnavailableError(RuntimeError):
    """Прокси не отвечает — Telethon connect запрещён."""

    def __init__(self, account: str, detail: str, proxy_url: str) -> None:
        self.account = account
        self.detail = detail
        self.proxy_url = proxy_url
        endpoint = mask_proxy_endpoint(proxy_url)
        super().__init__(f"{account}: прокси {endpoint} — {detail}")


def proxy_probe_enabled() -> bool:
    raw = os.environ.get("TELETHON_PROXY_PROBE", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def proxy_probe_timeout_sec() -> float:
    raw = os.environ.get("TELETHON_PROXY_PROBE_TIMEOUT", "8").strip()
    try:
        return max(2.0, min(30.0, float(raw)))
    except ValueError:
        return 8.0


def proxy_alert_cooldown_sec() -> float:
    raw = os.environ.get("TELETHON_PROXY_ALERT_COOLDOWN", "300").strip()
    try:
        return max(60.0, float(raw))
    except ValueError:
        return 300.0


def proxy_host_port(proxy_url: str) -> tuple[str, int]:
    normalized = normalize_proxy_url(proxy_url)
    parsed = urlparse(normalized)
    host = parsed.hostname
    if not host:
        raise ValueError(f"прокси: нет хоста в {proxy_url!r}")
    scheme = (parsed.scheme or "http").lower()
    port = parsed.port or (8080 if scheme in ("http", "https") else 1080)
    return host, port


def mask_proxy_endpoint(proxy_url: str) -> str:
    try:
        host, port = proxy_host_port(proxy_url)
        return f"{host}:{port}"
    except ValueError:
        return "(прокси)"


def probe_proxy_tcp(proxy_url: str, *, timeout: float | None = None) -> tuple[bool, str]:
    """Проверка, что до host:port прокси достучаться (не Telegram)."""
    if timeout is None:
        timeout = proxy_probe_timeout_sec()
    try:
        host, port = proxy_host_port(proxy_url)
    except ValueError as exc:
        return False, str(exc)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)
        sock.connect((host, port))
        return True, f"TCP {host}:{port} OK"
    except OSError as exc:
        return False, f"TCP {host}:{port}: {exc}"
    finally:
        sock.close()


def _try_alert_owner(text: str) -> None:
    try:
        from config import load_config
        from health_check import send_owner_text

        cfg = load_config()
    except SystemExit:
        return
    except Exception as exc:
        print(f"[!] Алерт: load_config: {exc}", flush=True)
        return

    ok, err = send_owner_text(cfg, text)
    if not ok:
        print(f"[!] Алерт боту не ушёл: {err}", flush=True)


def _format_proxy_alert(failures: list[tuple[str, str, str]]) -> str:
    lines = ["⛔ RawLead · прокси недоступен", ""]
    for account, detail, proxy_url in failures:
        lines.append(f"{account}: {mask_proxy_endpoint(proxy_url)} — {detail}")
    lines.extend(
        [
            "",
            "Telethon не подключаем (без домашнего IP). Бот и пульт живы — ждём прокси.",
            "Когда прокси восстановится, мониторинг поднимется сам. Или пульт ▶ заново.",
        ]
    )
    return "\n".join(lines)


def _maybe_alert_proxy_down(failures: list[tuple[str, str, str]]) -> None:
    global _last_proxy_alert_at, _last_proxy_alert_key
    if not failures:
        return
    key = ";".join(f"{a}:{mask_proxy_endpoint(p)}" for a, _, p in failures)
    now = time.time()
    if (
        now - _last_proxy_alert_at < proxy_alert_cooldown_sec()
        and key == _last_proxy_alert_key
    ):
        return
    _last_proxy_alert_at = now
    _last_proxy_alert_key = key
    _try_alert_owner(_format_proxy_alert(failures))


def list_active_monitor_proxy_failures() -> list[tuple[str, str, str]]:
    """(account, detail, proxy_url) для acc с chat_ids, у которых прокси не отвечает."""
    if not proxy_probe_enabled():
        return []
    from config import load_tg_monitor_config
    from tg_client import resolve_telethon_account

    tg_cfg = load_tg_monitor_config()
    failures: list[tuple[str, str, str]] = []
    for acfg in tg_cfg.accounts:
        if not acfg.chat_ids:
            continue
        _, _, proxy_url = resolve_telethon_account(acfg.account)
        ok, detail = probe_proxy_tcp(proxy_url)
        if not ok:
            failures.append((acfg.account, detail, proxy_url))
    return failures


def require_proxy_live(account: str, proxy_url: str) -> None:
    if not proxy_probe_enabled():
        return
    ok, detail = probe_proxy_tcp(proxy_url)
    if not ok:
        raise ProxyUnavailableError(account, detail, proxy_url)


def wait_active_monitor_proxies_live(
    *,
    log_fn: Callable[[str], None] | None = None,
    sleep_sec: float = 30.0,
) -> None:
    """Ждём прокси; процесс tg_main не завершаем (бот poll продолжает работать)."""
    while True:
        failures = list_active_monitor_proxy_failures()
        if not failures:
            if log_fn:
                log_fn("тг:прокси:ok — мониторинг продолжаем")
            return
        _maybe_alert_proxy_down(failures)
        accounts = ", ".join(f[0] for f in failures)
        msg = f"тг:прокси:wait accounts={accounts} sleep_sec={int(sleep_sec)}"
        if log_fn:
            log_fn(msg)
        else:
            print(msg, flush=True)
        time.sleep(max(5.0, sleep_sec))
