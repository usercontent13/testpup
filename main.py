from flask import Flask, jsonify
from pyppeteer import launch
import asyncio
import os

app = Flask(__name__)

@app.route('/')
def puppeteer_test():
    try:
        result = asyncio.run(get_page_title())
        return jsonify({"title": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def get_page_title():
    try:
        # Set a writable directory for Pyppeteer to store Chromium
        browser = await launch(
            headless=True, 
            args=["--no-sandbox", "--disable-setuid-sandbox"],
            executablePath=os.getenv("PUPPETEER_EXECUTABLE_PATH", None)  # Set Chromium path explicitly
        )
        page = await browser.newPage()
        await page.goto('https://example.com')
        title = await page.title()
        await browser.close()
        return title
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve page title: {str(e)}")

if __name__ == "__main__":
    app.run(debug=True)

