"""One-shot: HTML баннеры Яндекс.Директ → PNG 1080×1080."""
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "docs/design/yandex-direct"
DST = ROOT / "docs/design/assets/yandex-direct"
DST.mkdir(parents=True, exist_ok=True)

BANNERS = [
    ("banner-v1-feed.html", "banner-v1-feed.png"),
    ("banner-v2-draft.html", "banner-v2-draft.png"),
    ("banner-v3-match.html", "banner-v3-match.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for html_name, png_name in BANNERS:
        html_abs = (SRC / html_name).resolve().as_posix()
        png_abs = str(DST / png_name)
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.goto(f"file:///{html_abs}")
        page.wait_for_timeout(1200)  # wait for Google Fonts
        page.screenshot(
            path=png_abs,
            clip={"x": 0, "y": 0, "width": 1080, "height": 1080},
        )
        print(f"OK {png_name}")
    browser.close()

print("Done:", DST)
