from pyppeteer import launch
import asyncio

async def main():
    browser = await launch(headless=True)
    page = await browser.newPage()
    await page.goto('https://ytdata.vercel.app')
    title = await page.title()
    print(f"Page Title: {title}")
    await browser.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
