#!/usr/bin/env python3
"""Set subscription state for E2E / owner ops (@RawLead test persona).

Examples:
  python scripts/set_subscription_state.py --vps --username RawLead --plan free --mark-trial-used
  python scripts/set_subscription_state.py --vps --username RawLead --plan trial
  python scripts/set_subscription_state.py --vps --user-id 8d5afb3d-... --plan agent --days 30
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(_ROOT / ".env", override=False)
    load_dotenv(_ROOT / ".env.site", override=False)
except ImportError:
    pass

import psycopg  # noqa: E402

from trial_subscription import TRIAL_DAYS  # noqa: E402

RAWLEAD_TEST_USER_ID = "8d5afb3d-e8bd-4970-a33d-21c3ddeafdef"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_user_id(cur, *, username: str | None, user_id: str | None) -> str:
    if user_id:
        return user_id
    uname = (username or "").lstrip("@").lower()
    if not uname:
        raise SystemExit("need --username or --user-id")
    cur.execute(
        """
        SELECT id::text
        FROM users
        WHERE LOWER(COALESCE(tg_username, '')) = %s
        ORDER BY created_at NULLS LAST
        LIMIT 1
        """,
        (uname,),
    )
    row = cur.fetchone()
    if not row:
        raise SystemExit(f"user @{uname} not found")
    return str(row[0])


def _ensure_migration(cur) -> None:
    sql_path = _ROOT / "sql" / "025_prepaid_subscription.sql"
    if sql_path.is_file():
        cur.execute(sql_path.read_text(encoding="utf-8"))


def _set_state(
    cur,
    user_id: str,
    *,
    plan: str,
    days: int,
    mark_trial_used: bool,
    clear_trial_used: bool,
) -> None:
    ref = _utc_now()
    if plan == "free":
        cur.execute(
            """
            INSERT INTO subscriptions (user_id, plan, is_active)
            VALUES (%s::uuid, 'free', FALSE)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = 'free',
                is_active = FALSE,
                active_until = NULL,
                paused_until = NULL,
                paid_active_until = NULL
            """,
            (user_id,),
        )
        if mark_trial_used:
            cur.execute(
                """
                UPDATE subscriptions
                SET trial_used_at = COALESCE(trial_used_at, %s)
                WHERE user_id = %s::uuid
                """,
                (ref, user_id),
            )
        if clear_trial_used:
            cur.execute(
                "UPDATE subscriptions SET trial_used_at = NULL WHERE user_id = %s::uuid",
                (user_id,),
            )
        return

    if plan == "trial":
        until = ref + timedelta(days=TRIAL_DAYS)
        cur.execute(
            """
            INSERT INTO subscriptions (
                user_id, plan, is_active, active_until, trial_used_at, paid_active_until
            )
            VALUES (%s::uuid, 'trial', TRUE, %s, %s, NULL)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = 'trial',
                is_active = TRUE,
                active_until = EXCLUDED.active_until,
                paused_until = NULL,
                paid_active_until = NULL,
                trial_used_at = COALESCE(subscriptions.trial_used_at, EXCLUDED.trial_used_at)
            """,
            (user_id, until, ref),
        )
        return

    if plan in ("agent", "beta", "pro"):
        until = ref + timedelta(days=max(1, days))
        cur.execute(
            """
            INSERT INTO subscriptions (
                user_id, plan, is_active, active_until, paid_active_until
            )
            VALUES (%s::uuid, %s, TRUE, %s, NULL)
            ON CONFLICT (user_id) DO UPDATE
            SET plan = EXCLUDED.plan,
                is_active = TRUE,
                active_until = EXCLUDED.active_until,
                paused_until = NULL,
                paid_active_until = NULL
            """,
            (user_id, plan, until),
        )
        return

    raise SystemExit(f"unsupported plan: {plan}")


def _print_state(cur, user_id: str) -> None:
    cur.execute(
        """
        SELECT u.tg_username, s.plan, s.is_active, s.active_until, s.trial_used_at, s.paid_active_until
        FROM subscriptions s
        JOIN users u ON u.id = s.user_id
        WHERE s.user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        print(f"user_id={user_id} (no subscription row)")
        return
    print(
        f"user_id={user_id} @{row[0] or '?'} "
        f"plan={row[1]} active={row[2]} until={row[3]} "
        f"trial_used_at={row[4]} prepaid_until={row[5]}"
    )


def _load_database_url() -> str:
    for name in (".env.site", ".env"):
        path = _ROOT / name
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            if key.strip() != "DATABASE_URL":
                continue
            url = val.strip().strip('"').strip("'")
            if url and "neon.tech" not in url.lower():
                return url
    url = os.getenv("DATABASE_URL", "").strip()
    if url and "neon.tech" not in url.lower():
        return url
    return ""


def _run_local(args: argparse.Namespace) -> int:
    db_url = _load_database_url()
    if not db_url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            if args.migrate:
                _ensure_migration(cur)
            user_id = _resolve_user_id(cur, username=args.username, user_id=args.user_id)
            if args.dry_run:
                print(f"DRY: would set {user_id} -> {args.plan}")
                return 0
            _set_state(
                cur,
                user_id,
                plan=args.plan,
                days=args.days,
                mark_trial_used=args.mark_trial_used,
                clear_trial_used=args.clear_trial_used,
            )
            conn.commit()
            _print_state(cur, user_id)
    return 0


def _run_vps(args: argparse.Namespace) -> int:
    import deploy_vps_ssh as ssh  # noqa: E402

    remote_script = "/opt/rawlead/scripts/set_subscription_state.py"
    ssh.upload(_ROOT / "scripts" / "set_subscription_state.py", remote_script)
    ssh.upload(_ROOT / "sql" / "025_prepaid_subscription.sql", "/opt/rawlead/sql/025_prepaid_subscription.sql")

    cmd_parts = [
        "cd /opt/rawlead",
        "&&",
        "sudo -u rawlead env PYTHONPATH=/opt/rawlead/src",
        ".venv/bin/python",
        remote_script,
        "--migrate",
    ]
    if args.username:
        cmd_parts.extend(["--username", shlex.quote(args.username)])
    if args.user_id:
        cmd_parts.extend(["--user-id", shlex.quote(args.user_id)])
    cmd_parts.extend(["--plan", shlex.quote(args.plan)])
    if args.days != 30:
        cmd_parts.extend(["--days", str(args.days)])
    if args.mark_trial_used:
        cmd_parts.append("--mark-trial-used")
    if args.clear_trial_used:
        cmd_parts.append("--clear-trial-used")
    if args.dry_run:
        cmd_parts.append("--dry-run")

    cmd = " ".join(cmd_parts)
    _, out, err = ssh.run(cmd, check=False)
    text = (out or "") + (err or "")
    print(text.strip())
    return 0 if "user_id=" in text or args.dry_run else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Set subscription state (E2E / ops)")
    parser.add_argument("--username", default="RawLead", help="TG username without @")
    parser.add_argument("--user-id", default="", help=f"uuid (test persona: {RAWLEAD_TEST_USER_ID})")
    parser.add_argument(
        "--plan",
        required=True,
        choices=("free", "trial", "agent", "beta", "pro"),
    )
    parser.add_argument("--days", type=int, default=30, help="For agent/beta/pro")
    parser.add_argument(
        "--mark-trial-used",
        action="store_true",
        help="With free: block auto-trial on next login",
    )
    parser.add_argument(
        "--clear-trial-used",
        action="store_true",
        help="With free: allow auto-trial again",
    )
    parser.add_argument("--migrate", action="store_true", help="Apply sql/025_prepaid_subscription.sql if needed")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--vps", action="store_true", help="Run on prod VPS via SSH")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if args.vps:
        return _run_vps(args)
    if not args.migrate:
        args.migrate = True
    return _run_local(args)


if __name__ == "__main__":
    raise SystemExit(main())
