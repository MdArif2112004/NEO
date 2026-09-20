import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await page.goto("https://www.herecomestheguide.com/wedding-venues/california", 
                       wait_until="networkidle", timeout=40000)
        await page.wait_for_timeout(3000)
        
        # Dump all links that look like venue pages
        links = await page.query_selector_all("a[href]")
        venue_links = []
        for link in links:
            href = await link.get_attribute("href") or ""
            text = (await link.inner_text()).strip()
            if "/wedding-venues/" in href and text:
                venue_links.append(f"{text} | {href}")
        
        with open("hctg_debug.txt", "w", encoding="utf-8") as f:
            f.write(f"Total venue links found: {len(venue_links)}\n\n")
            f.write("\n".join(venue_links[:50]))
        
        print(f"Found {len(venue_links)} venue links")
        print("Saved to hctg_debug.txt")
        await browser.close()

asyncio.run(main())