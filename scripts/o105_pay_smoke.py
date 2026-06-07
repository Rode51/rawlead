#!/usr/bin/env python3
"""O105-w1 smoke: pay menu → pending → owner notify → approve (dry-run safe)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from config import load_config_for_profile  # noqa: E402
from premium_pay import (  # noqa: E402
    _load_pending,
    _set_pending_status,
    create_pending,
    format_pay_menu,
    notify_owner_pending,
    pay_available,
    send_pay_method,
)
from stars_billing import activate_subscription  # noqa: E402


def _table_ok(db_url: str) -> bool:
    import psycopg

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'payment_pending'
                """
            )
            return cur.fetchone() is not None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tg-user-id", type=int, default=0, help="Test TG user id (default: TELEGRAM_CHAT_ID)")
    ap.add_argument("--method", choices=("menu", "sbp", "crypto", "stars"), default="sbp")
    ap.add_argument("--deep-link", action="store_true", help="Use send_pay_method (as start=pay_*)")
    ap.add_argument("--approve", action="store_true", help="Auto-approve after notify (no FLPARSING click)")
    ap.add_argument("--send-menu", action="store_true", help="Send /pay menu to chat via Bot API")
    args = ap.parse_args()

    cfg = load_config_for_profile("site")
    db = cfg.database_url.strip()
    if not db:
        print("FAIL: DATABASE_URL empty")
        return 1
    if not _table_ok(db):
        print("FAIL: payment_pending table missing — run sql/017_payment_pending.sql")
        return 1
    print("OK: payment_pending exists")

    if not pay_available(cfg):
        print("FAIL: pay not configured (PAY_* env)")
        return 1
    print(f"OK: pay_available rub={cfg.pay_premium_rub}")

    tg_user = args.tg_user_id or int(cfg.telegram_chat_id.strip())
    tg_chat = tg_user

    if args.send_menu or args.deep_link:
        errors: list[str] = []
        if args.deep_link:
            send_pay_method(cfg, tg_chat, tg_user, args.method, errors)
            print(f"OK: deep link method={args.method} chat={tg_chat} errors={errors}")
            if args.method in ("menu", "stars"):
                print("SMOKE OK (no pending for menu/stars)")
                return 0
        else:
            send_pay_method(cfg, tg_chat, tg_user, "menu", errors)
            print(f"OK: pay menu sent chat={tg_chat} errors={errors}")
            return 0

    if args.method in ("menu", "stars"):
        print("SKIP pending: use --deep-link for menu/stars")
        return 0

    pending_id, err = create_pending(
        cfg,
        tg_user_id=tg_user,
        tg_chat_id=tg_chat,
        method=args.method,
    )
    if pending_id is None:
        print(f"FAIL: create_pending: {err}")
        return 1
    print(f"OK: pending #{pending_id} method={args.method} tg={tg_user}")

    pending = _load_pending(db, pending_id)
    if not pending:
        print("FAIL: load pending")
        return 1

    _set_pending_status(db, pending_id, "awaiting_owner", owner_notified=True)
    ok, detail = notify_owner_pending(cfg, pending)
    print(f"{'OK' if ok else 'WARN'}: owner notify detail={detail}")

    if args.approve:
        ok_act = activate_subscription(
            db,
            tg_user_id=tg_user,
            tg_chat_id=tg_chat,
            days=cfg.stars_subscription_days,
        )
        if ok_act:
            _set_pending_status(db, pending_id, "approved")
            print(f"OK: subscription activated {cfg.stars_subscription_days}d tg={tg_user}")
        else:
            print("FAIL: activate_subscription")
            return 1

    print("SMOKE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
