from flask import Flask, jsonify
from pyppeteer import launch
import asyncio

app = Flask(__name__)

@app.route('/')
def puppeteer_test():
    try:
        result = asyncio.run(get_page_title())
        return jsonify({"title": result})
    except Exception as e:
        # Log the error for debugging
        return jsonify({"error": str(e)}), 500

async def get_page_title():
    try:
        browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.newPage()
        await page.goto('https://example.com')
        title = await page.title()
        await browser.close()
        return title
    except Exception as e:
        raise RuntimeError(f"Failed to retrieve page title: {str(e)}")

if __name__ == "__main__":
    # Enable debug mode for local testing
    app.run(debug=True)

