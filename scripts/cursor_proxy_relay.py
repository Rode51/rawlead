"""Локальный relay для Cursor — автопереключение upstream без перезапуска IDE.

  scripts\\start-cursor-proxy-relay.bat   — фон + один раз прописать 127.0.0.1 в Cursor
  .venv\\Scripts\\python.exe scripts\\cursor_proxy_relay.py --probe-only

Env: CURSOR_PROXY_RELAY=1 · CURSOR_PROXY_RELAY_PORT=18777 · CURSOR_PROXY_POOL_URLS=...
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    enc = getattr(_stream, "encoding", None) or ""
    if enc.lower() != "utf-8":
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError, ValueError):
            pass

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from config import normalize_proxy_url  # noqa: E402

# ВАЖНО: модуль-имя `cursor_proxy_relay.py` существует и в `scripts/`, и в `src/`.
# Поэтому обычный `import cursor_proxy_relay` даёт циклический импорт.
# Загружаем реализацию из `src/cursor_proxy_relay.py` по пути под отдельным именем.
import importlib.util  # noqa: E402

_impl_path = _ROOT / "src" / "cursor_proxy_relay.py"
_spec = importlib.util.spec_from_file_location("cursor_proxy_relay_impl", _impl_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Can't load relay implementation from {_impl_path}")
_mod = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _mod
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

CursorProxyRelay = _mod.CursorProxyRelay  # type: ignore[attr-defined]
parse_upstream_pool = _mod.parse_upstream_pool  # type: ignore[attr-defined]
probe_pool = _mod.probe_pool  # type: ignore[attr-defined]
from dotenv import load_dotenv  # noqa: E402
from proxy_probe import mask_proxy_endpoint  # noqa: E402

_LOG = _ROOT / "data" / "cursor_proxy_relay.log"


def _pool_from_env() -> list[str]:
    raw = os.environ.get("CURSOR_PROXY_POOL_URLS", "").strip()
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    out: list[str] = []
    for key in (
        "CURSOR_PROXY_URL",
        "CURSOR_PROXY_FALLBACK_URLS",
        "TG_PROXY_URL",
    ):
        val = os.environ.get(key, "").strip()
        if not val:
            continue
        if key == "CURSOR_PROXY_FALLBACK_URLS":
            out.extend(p.strip() for p in val.split(",") if p.strip())
        else:
            out.append(val)
    for acc in ("ACC1", "ACC2", "ACC3"):
        v = os.environ.get(f"TELETHON_PROXY_{acc}", "").strip()
        if v:
            out.append(v)
    return out


def _relay_port() -> int:
    raw = os.environ.get("CURSOR_PROXY_RELAY_PORT", "18777").strip()
    try:
        return max(1024, min(65535, int(raw)))
    except ValueError:
        return 18777


def cmd_probe_only(pool_raw: list[str]) -> int:
    pool = parse_upstream_pool(pool_raw)
    if not pool:
        print("FAIL: пустой CURSOR_PROXY_POOL_URLS", file=sys.stderr)
        return 1
    print("TCP probe pool (Cursor relay):")
    ok_any = False
    for u, alive in zip(pool, probe_pool(pool)):
        mark = "OK" if alive else "FAIL"
        print(f"  {u.endpoint:<22} {mark}")
        ok_any = ok_any or alive
    return 0 if ok_any else 1


def cmd_sync_localhost() -> int:
    from sync_cursor_proxy import (  # noqa: E402
        _CURSOR_SETTINGS,
        _apply_proxy_settings,
        _load_settings,
        _save_settings,
    )

    port = _relay_port()
    local = f"http://127.0.0.1:{port}"
    settings = _load_settings(_CURSOR_SETTINGS)
    _apply_proxy_settings(settings, local)
    _save_settings(_CURSOR_SETTINGS, settings)
    print(f"Cursor settings -> {local}")
    print("Перезапусти Cursor ОДИН РАЗ после первого включения relay.")
    print("Дальше relay сам меняет upstream — перезапуск не нужен.")
    return 0


def main() -> int:
    load_dotenv(_ROOT / ".env")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(_LOG, encoding="utf-8"),
        ],
    )

    parser = argparse.ArgumentParser(description="Cursor local proxy relay")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--sync-localhost", action="store_true")
    args = parser.parse_args()

    pool_raw = _pool_from_env()
    if args.probe_only:
        return cmd_probe_only(pool_raw)

    if args.sync_localhost:
        return cmd_sync_localhost()

    pool = parse_upstream_pool(pool_raw)
    if not pool:
        print("FAIL: задай CURSOR_PROXY_POOL_URLS в .env", file=sys.stderr)
        return 1

    port = _relay_port()
    relay = CursorProxyRelay(pool, bind_port=port)
    print(f"Relay {relay.listen_addr} | pool {len(pool)}")
    print("Log:", _LOG)
    try:
        relay.serve_forever()
    except KeyboardInterrupt:
        relay.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
