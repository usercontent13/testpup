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
        return jsonify({"error": str(e)}), 500

async def get_page_title():
    browser = await launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
    page = await browser.newPage()
    await page.goto('https://example.com')
    title = await page.title()
    await browser.close()
    return title

# Vercel requires this `app` variable for routing
app = app
