"""
Grab targeted screenshots from rawlead.ru for portfolio case study.
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

OUT = Path(__file__).parent.parent / "public" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

URL = "https://rawlead.ru"

async def shot(page, name, selector=None, clip=None):
    try:
        if selector:
            el = page.locator(selector).first
            await el.screenshot(path=str(OUT / name), timeout=5000)
        else:
            await page.screenshot(path=str(OUT / name), clip=clip, full_page=False)
        size = (OUT / name).stat().st_size // 1024
        print(f"  + {name}  {size}KB")
    except Exception as e:
        print(f"  ! {name} failed: {e}")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Desktop 1440px retina
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(2000)

        # Screenshot 1: "ТВОЯ ЛЕНТА" dark section — scroll to it
        # It appears around 60-65% scroll depth on the page
        total_h = await page.evaluate("document.body.scrollHeight")
        target_y = int(total_h * 0.38)
        await page.evaluate(f"window.scrollTo(0, {target_y})")
        await page.wait_for_timeout(700)
        await shot(page, "rawlead-your-feed.png", clip={"x": 0, "y": 0, "width": 1440, "height": 900})

        # Screenshot 2: Live orders cards section
        target_y2 = int(total_h * 0.18)
        await page.evaluate(f"window.scrollTo(0, {target_y2})")
        await page.wait_for_timeout(700)
        await shot(page, "rawlead-orders.png", clip={"x": 0, "y": 0, "width": 1440, "height": 900})

        # Screenshot 3: Hero (for context)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(500)
        await shot(page, "rawlead-hero.png", clip={"x": 0, "y": 0, "width": 1440, "height": 820})

        await ctx.close()
        await browser.close()
        print("\nDone.")

asyncio.run(main())
