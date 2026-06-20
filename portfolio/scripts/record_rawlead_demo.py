"""
Record a scrolling demo of rawlead.ru as WebM video.
Output: public/rawlead-demo.webm
"""
import asyncio
import shutil
from pathlib import Path
from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).parent.parent / "public"
OUT_DIR.mkdir(exist_ok=True)

URL = "https://rawlead.ru"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            device_scale_factor=1,
            record_video_dir=str(OUT_DIR / "_tmp_video"),
            record_video_size={"width": 1280, "height": 720},
        )

        page = await ctx.new_page()
        await page.goto(URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1200)   # pause on hero

        total_h = await page.evaluate("document.body.scrollHeight")

        # Slow scroll — hero → feed cards → твоя лента
        steps = [
            (0,                    1000),   # hero pause
            (int(total_h * 0.10),  600),
            (int(total_h * 0.18),  900),   # live orders section
            (int(total_h * 0.25),  600),
            (int(total_h * 0.33),  900),   # dark section / твоя лента
            (int(total_h * 0.40),  800),
            (int(total_h * 0.44),  600),
            (int(total_h * 0.38),  400),   # scroll back up a bit
            (int(total_h * 0.33),  1200),  # hold on твоя лента
        ]

        for y, wait_ms in steps:
            await page.evaluate(f"window.scrollTo({{top: {y}, behavior: 'smooth'}})")
            await page.wait_for_timeout(wait_ms)

        # Close context — this finalises the video file
        await ctx.close()
        await browser.close()

        # Move video from tmp dir to public/
        tmp = Path(OUT_DIR / "_tmp_video")
        videos = list(tmp.glob("*.webm"))
        if videos:
            src = videos[0]
            dst = OUT_DIR / "rawlead-demo.webm"
            shutil.move(str(src), str(dst))
            size_kb = dst.stat().st_size // 1024
            print(f"Saved: {dst}  ({size_kb} KB)")
        else:
            print("No video found in tmp dir")

        # Cleanup
        shutil.rmtree(str(tmp), ignore_errors=True)

asyncio.run(main())
