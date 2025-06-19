# screenshot.py
import sys
import asyncio
import os
from pyppeteer import launch

THUMB_DIR = "static/thumbnails"
os.makedirs(THUMB_DIR, exist_ok=True)

async def main(name, url):
    path = os.path.join(THUMB_DIR, f"{name}.png")
    if os.path.exists(path):
        return

    try:
        browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.newPage()
        await page.goto(url, {'waitUntil': 'networkidle2', 'timeout': 10000})
        await page.setViewport({'width': 800, 'height': 400})
        await page.screenshot({'path': path})
        await browser.close()
    except Exception as e:
        print(f"[ERROR] Screenshot generation failed: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python screenshot.py <name> <url>")
        sys.exit(1)
    name = sys.argv[1]
    url = sys.argv[2]
    asyncio.run(main(name, url))
