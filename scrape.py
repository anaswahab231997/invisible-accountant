import asyncio
from playwright.async_api import async_playwright

async def scrape():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        print("Loading Trustpilot...")
        await page.goto('https://uk.trustpilot.com/review/xero.com?stars=1', wait_until='networkidle')
        reviews = await page.evaluate('''() => {
            let elements = document.querySelectorAll('p[data-service-review-text-typography="true"]');
            let res = [];
            for(let i=0; i<4; i++) {
                if(elements[i]) res.push(elements[i].innerText);
            }
            return res;
        }''')
        print('XERO REVIEWS:')
        for r in reviews: print('-', r)
        
        print("Loading Dext Trustpilot...")
        await page.goto('https://uk.trustpilot.com/review/dext.com?stars=1', wait_until='networkidle')
        dext_reviews = await page.evaluate('''() => {
            let elements = document.querySelectorAll('p[data-service-review-text-typography="true"]');
            let res = [];
            for(let i=0; i<4; i++) {
                if(elements[i]) res.push(elements[i].innerText);
            }
            return res;
        }''')
        print('DEXT REVIEWS:')
        for r in dext_reviews: print('-', r)
        
        await browser.close()

asyncio.run(scrape())
