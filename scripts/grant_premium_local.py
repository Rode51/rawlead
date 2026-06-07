#!/usr/bin/env python3
"""Grant temporary Premium in Neon + mint local login snippet (dev UI only)."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=False)

import psycopg  # noqa: E402
from jwt_auth import issue_access_token  # noqa: E402


def _snippet(token: str) -> str:
    return (
        "localStorage.setItem('rawlead_access_token',"
        + repr(token)
        + ");document.cookie='rl_access='+encodeURIComponent("
        + repr(token)
        + ")+'; path=/; max-age=604800; samesite=lax';location.reload();"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--username",
        default="rcnn43",
        help="Telegram username without @ (default: rcnn43)",
    )
    parser.add_argument(
        "--plan",
        default="beta",
        choices=("beta", "agent", "trial"),
        help="Premium plan to grant (default: beta)",
    )
    parser.add_argument("--days", type=int, default=30, help="Active days (default: 30)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    db_url = os.getenv("DATABASE_URL", "").strip()
    if not db_url:
        print("DATABASE_URL missing", file=sys.stderr)
        return 1

    username = args.username.lstrip("@").lower()
    until = datetime.now(timezone.utc) + timedelta(days=max(1, args.days))

    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, tg_user_id, tg_username
                FROM users
                WHERE LOWER(COALESCE(tg_username, '')) = %s
                ORDER BY created_at NULLS LAST
                LIMIT 1
                """,
                (username,),
            )
            row = cur.fetchone()
            if not row:
                print(f"User @{username} not found in Neon", file=sys.stderr)
                return 1
            user_id, tg_user_id, tg_username = str(row[0]), int(row[1]), row[2]

            if args.plan == "trial":
                cur.execute(
                    """
                    INSERT INTO subscriptions (
                        user_id, plan, is_active, active_until, paused_until, trial_used_at
                    )
                    VALUES (%s::uuid, 'trial', TRUE, %s, NULL, NOW())
                    ON CONFLICT (user_id) DO UPDATE
                    SET plan = 'trial',
                        is_active = TRUE,
                        active_until = EXCLUDED.active_until,
                        paused_until = NULL,
                        trial_used_at = COALESCE(subscriptions.trial_used_at, NOW())
                    """,
                    (user_id, until),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO subscriptions (
                        user_id, plan, is_active, active_until, paused_until
                    )
                    VALUES (%s::uuid, %s, TRUE, %s, NULL)
                    ON CONFLICT (user_id) DO UPDATE
                    SET plan = EXCLUDED.plan,
                        is_active = TRUE,
                        active_until = EXCLUDED.active_until,
                        paused_until = NULL
                    """,
                    (user_id, args.plan, until),
                )
        conn.commit()

    token = issue_access_token(user_id, tg_user_id=tg_user_id)
    snippet = _snippet(token)
    out_snippet = _ROOT / "data" / "_local_premium_login_snippet.js"
    out_token = _ROOT / "data" / "_local_premium_token.txt"
    out_token.write_text(token + "\n", encoding="utf-8")
    out_snippet.write_text(snippet + "\n", encoding="utf-8")

    print(f"user_id={user_id}")
    print(f"tg_username=@{tg_username or username}")
    print(f"plan={args.plan} until={until.date().isoformat()}")
    print(f"snippet={out_snippet}")
    print(snippet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
