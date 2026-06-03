#!/usr/bin/env python3
"""Smoke O105-WP on prod."""
from __future__ import annotations

import urllib.request

URLS = {
    "home": "https://rawlead.ru/",
    "pricing": "https://rawlead.ru/pricing/",
    "faq": "https://rawlead.ru/faq/",
    "how": "https://rawlead.ru/how/",
    "lenta": "https://rawlead.ru/lenta/",
}


def fetch(url: str) -> str:
    return urllib.request.urlopen(url, timeout=25).read().decode("utf-8", "replace")


def main() -> int:
    pages = {k: fetch(u) for k, u in URLS.items()}
    home = pages["home"]
    pricing = pages["pricing"]
    faq = pages["faq"]
    how = pages["how"]
    lenta = pages["lenta"]
    checks = {
        "home_trust_strip": "rl-trust-strip" in home,
        "home_790": "790" in home,
        "home_pricing_preview": "pricing-preview" in home,
        "home_ver_1183": "1.18.3" in home,
        "pricing_790": "790" in pricing,
        "pricing_payment_block": "rl-payment-block" in pricing,
        "pricing_full_card": "rl-price-card--full" in pricing,
        "pricing_pay_deeplink": "start=pay" in pricing,
        "faq_790_q7": "790" in faq and "Сервис платный" in faq,
        "faq_q8_slots": "лимит 10" in faq.lower() or "10 отклик" in faq.lower(),
        "faq_q9_trial": "пробный" in faq.lower() or "3 дня" in faq,
        "how_790": "790" in how,
        "lenta_feed_js_1183": "rawlead-feed.js?ver=1.18.3" in lenta,
        "lenta_anon_two_speeds": "Premium — сразу, от 790" in lenta and "/pricing/" in lenta,
        "lenta_delay_el": "rl-feed-delay-notice" in lenta,
        "lenta_slot_css": "rl-feed-card__slot-line" in lenta or "1.18.3" in lenta,
    }
    for k, v in checks.items():
        print(f"{k}: {'OK' if v else 'FAIL'}")
    ok = all(checks.values())
    print("ALL OK" if ok else "SOME FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
