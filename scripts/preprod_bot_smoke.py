"""O37b: smoke @rawlead_bot — getMe, /status (Telethon acc), отчёт JSON."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "src"))

_DEFAULT_OUT = _ROOT / "data" / "preprod_bot_smoke.json"


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        for name in (".env.site", ".env"):
            p = _ROOT / name
            if p.is_file():
                load_dotenv(p, override=(name == ".env.site"))
    except ImportError:
        pass


def _bot_get_me(token: str, *, cfg: Any) -> dict:
    import requests

    from config import telegram_requests_proxies

    proxies = telegram_requests_proxies(cfg)
    url = f"https://api.telegram.org/bot{token}/getMe"
    resp = requests.get(url, proxies=proxies, timeout=20)
    data = resp.json()
    return {
        "ok": bool(data.get("ok")),
        "username": (data.get("result") or {}).get("username"),
        "id": (data.get("result") or {}).get("id"),
        "http_status": resp.status_code,
        "error": data.get("description") if not data.get("ok") else None,
    }


async def _telethon_status_smoke(account: str) -> dict:
    from tg_client import connect_client

    out: dict = {"account": account, "ok": False}
    try:
        client = await connect_client(account)
    except Exception as exc:
        out["error"] = str(exc)[:200]
        return out
    try:
        cfg_mod = __import__("config", fromlist=["load_config"])
        cfg = cfg_mod.load_config()
        me = _bot_get_me(cfg.telegram_bot_token.strip(), cfg=cfg)
        username = (me.get("username") or "").strip()
        if not username:
            out["error"] = me.get("error") or "bot getMe failed"
            return out
        entity = await client.get_entity(f"@{username.lstrip('@')}")
        await client.send_message(entity, "/status")
        await asyncio.sleep(2)
        msgs = await client.get_messages(entity, limit=3)
        texts = [(m.message or "")[:120] for m in msgs if m.out is False]
        out["ok"] = bool(texts)
        out["last_bot_replies"] = texts
    except Exception as exc:
        out["error"] = str(exc)[:200]
    finally:
        await client.disconnect()
    return out


async def _telethon_start_smoke(account: str) -> dict:
    from tg_bot_start import ensure_bot_started
    from tg_client import connect_client

    out: dict = {"account": account, "ok": False}
    try:
        client = await connect_client(account)
    except Exception as exc:
        out["error"] = str(exc)[:200]
        return out
    try:
        ok = await ensure_bot_started(client, account, force=True)
        out["ok"] = ok
    except Exception as exc:
        out["error"] = str(exc)[:200]
    finally:
        await client.disconnect()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="O37b bot smoke @rawlead_bot")
    parser.add_argument("--output", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--account", default="acc1", choices=("acc1", "acc2", "acc3"))
    parser.add_argument("--skip-telethon", action="store_true")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    _load_env()
    from config import load_config

    cfg = load_config()
    token = cfg.telegram_bot_token.strip() or os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "bot": None,
        "start": None,
        "status": None,
        "pass": False,
    }

    if not token:
        report["bot"] = {"ok": False, "error": "TELEGRAM_BOT_TOKEN missing"}
    else:
        report["bot"] = _bot_get_me(token, cfg=cfg)

    if not args.skip_telethon:
        report["start"] = asyncio.run(_telethon_start_smoke(args.account))
        report["status"] = asyncio.run(_telethon_status_smoke(args.account))

    report["pass"] = bool(report.get("bot", {}).get("ok")) and (
        args.skip_telethon
        or (bool(report.get("status", {}).get("ok")))
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
