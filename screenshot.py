from pyppeteer import launch
import asyncio
import sys
import os
from pathlib import Path

async def generate_screenshot(url):
    browser = await launch(headless=True, args=["--no-sandbox"])
    page = await browser.newPage()
    await page.setViewport({'width': 1280, 'height': 720})
    try:
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 10000})
        screenshot = await page.screenshot({'type': 'png'})
    finally:
        await browser.close()
    return screenshot

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python screenshot.py <name> <url>")
        sys.exit(1)

    name, url = sys.argv[1], sys.argv[2]
    port = name.rsplit('_', 1)[-1]

    root = Path(__file__).resolve().parent
    path = root / "static" / "thumbnails" / f"{name}.png"

    async def save():
        print(f"[DEBUG] screenshot.py saving to: {path}")
        image_bytes = await generate_screenshot(url)
        if image_bytes:
            os.makedirs(path.parent, exist_ok=True)
            with open(path, 'wb') as f:
                f.write(image_bytes)

    asyncio.run(save())
