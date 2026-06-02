#!/usr/bin/env python3
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, "/opt/rawlead/src")
from dotenv import load_dotenv

load_dotenv("/opt/rawlead/.env")
load_dotenv("/opt/rawlead/.env.site", override=True)
from jwt_auth import issue_access_token
import psycopg

db = os.environ["DATABASE_URL"]
uid = "164786fe-b979-4bfa-a9dc-42416465f503"
tg_uid = 1342741103
token = issue_access_token(uid, tg_user_id=tg_uid)
print("token_ok", len(token))

for label, url in [
    ("local", "http://127.0.0.1:8000/v1/admin/dashboard"),
    ("https", "https://rawlead.ru/v1/admin/dashboard"),
    ("wp_ops", "https://rawlead.ru/wp-json/rawlead/v1/ops/dashboard"),
]:
    t0 = time.time()
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
        data = json.loads(body)
        print(
            label,
            resp.status,
            len(body),
            round(time.time() - t0, 2),
            "visits",
            data.get("today", {}).get("visits"),
        )
    except Exception as exc:
        print(label, "ERR", round(time.time() - t0, 2), exc)
