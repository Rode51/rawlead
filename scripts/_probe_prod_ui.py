#!/usr/bin/env python3
"""One-off prod HTML probe for O280 parity doc."""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

PAGES = {
    "home": "https://rawlead.ru/",
    "lenta": "https://rawlead.ru/lenta/",
    "cabinet": "https://rawlead.ru/cabinet/",
    "pricing": "https://rawlead.ru/pricing/",
}

KEYS = [
    "Кабинет",
    "Лента заказов",
    "Мои отклики",
    "Твои навыки",
    "RawLead Premium",
    "Уведомления",
    "Войти через Telegram",
    "Лента уже подбирает",
    "черновики",
    "790",
    "Заказы под твой стек",
    "Показать ещё",
    "Мимо",
    "Берем",
    "Пройти тест заново",
    "ИИ-агент",
    "rl-cabinet-notif",
    "rl-cabinet-user",
    "rl-cabinet-sub",
]


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, url in PAGES.items():
        html = urllib.request.urlopen(url, timeout=20).read().decode("utf-8", errors="replace")
        (out_dir / f"_probe_{name}.html").write_text(html, encoding="utf-8")
        ver = re.search(r"rawlead\.css\?ver=([\d.]+)", html)
        h1s = re.findall(r"<h1[^>]*>([^<]+)</h1>", html)
        h2s = re.findall(r"<h2[^>]*class=\"rl-[^\"]+\"[^>]*>([^<]+)</h2>", html)[:8]
        ids = sorted(set(re.findall(r'id="(rl-cabinet[^"]+)"', html)))
        print(f"=== {name} ===")
        print(f"  theme ver: {ver.group(1) if ver else '?'}")
        print(f"  h1: {h1s[:5]}")
        print(f"  h2 rl: {h2s}")
        print(f"  keys: {[k for k in KEYS if k in html]}")
        if ids:
            print(f"  cabinet ids ({len(ids)}): {ids[:12]}...")
        print()


if __name__ == "__main__":
    main()
