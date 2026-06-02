import os
import sys

sys.path.insert(0, "/opt/rawlead/src")
from dotenv import load_dotenv

load_dotenv("/opt/rawlead/.env")
import psycopg

db = os.environ["DATABASE_URL"]
with psycopg.connect(db) as conn:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.id, u.tg_user_id, u.tg_username, s.plan
            FROM users u
            LEFT JOIN subscriptions s ON s.user_id = u.id
            ORDER BY u.created_at DESC NULLS LAST
            LIMIT 8
            """
        )
        for r in cur.fetchall():
            print(r)
        cur.execute(
            """
            SELECT COUNT(*)::int FROM users u
            INNER JOIN subscriptions s ON s.user_id = u.id
            WHERE s.plan = 'owner'
            """
        )
        print("owner_plans", cur.fetchone()[0])
print("TELEGRAM_CHAT_ID set", bool(os.environ.get("TELEGRAM_CHAT_ID", "").strip()))
