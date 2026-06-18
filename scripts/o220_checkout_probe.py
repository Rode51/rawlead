#!/usr/bin/env python3
"""O220 r7: probe YooKassa checkout — API create + confirmation URL reachability (no secrets in output)."""

from __future__ import annotations

import base64
import json
import os
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_ROOT / ".env", override=False)
load_dotenv(_ROOT / ".env.site", override=False)

_ALLOWED_HOST_SUFFIX = ("yookassa.ru", "yoomoney.ru")


def _host_ok(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == sfx or host.endswith("." + sfx) for sfx in _ALLOWED_HOST_SUFFIX)


def main() -> int:
    sid = (os.environ.get("YOOKASSA_SHOP_ID") or "").strip()
    key = (os.environ.get("YOOKASSA_SECRET_KEY") or "").strip()
    if not sid or not key:
        print("SKIP: YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY not set locally")
        return 0

    auth = base64.b64encode(f"{sid}:{key}".encode()).decode()
    payload = {
        "amount": {"value": "1.00", "currency": "RUB"},
        "capture": True,
        "confirmation": {
            "type": "redirect",
            "return_url": "https://rawlead.ru/cabinet/?pay=return",
        },
        "description": "RawLead O220 checkout probe",
        "metadata": {"user_id": "probe", "kind": "trial"},
    }
    try:
        r = requests.post(
            "https://api.yookassa.ru/v3/payments",
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/json",
                "Idempotence-Key": str(uuid.uuid4()),
            },
            json=payload,
            timeout=30,
        )
    except requests.RequestException as exc:
        print(f"FAIL: api.yookassa.ru unreachable — {exc}")
        return 1

    print(f"api_status={r.status_code}")
    try:
        data = r.json()
    except json.JSONDecodeError:
        print("FAIL: non-JSON response from YooKassa API")
        return 1

    if r.status_code >= 400:
        print(f"FAIL: {data.get('description') or data.get('code') or 'gateway_error'}")
        return 1

    conf = data.get("confirmation") or {}
    url = str(conf.get("confirmation_url") or "").strip()
    if not url:
        print("FAIL: empty confirmation_url")
        return 1
    if not _host_ok(url):
        print(f"FAIL: unexpected confirmation host — {urlparse(url).hostname}")
        return 1

    print(f"confirmation_host={urlparse(url).hostname}")
    try:
        head = requests.head(url, timeout=20, allow_redirects=True)
        print(f"confirmation_head={head.status_code}")
        if head.status_code >= 500:
            print("WARN: payment page returned 5xx — owner network or YooMoney outage")
            return 2
    except requests.RequestException as exc:
        print(f"WARN: confirmation URL HEAD failed — {exc}")
        print("→ If API OK but browser timeout: likely client/network, escalate @mechanic")
        return 2

    print("PROBE OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
