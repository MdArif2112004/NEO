import asyncio
import csv
import random
import re
import time

INPUT_FILE = "california_venues.csv"
EMAIL_REGEX = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"

async def extract_email(page, url):
    try:
        await page.goto(url, timeout=20000)
        await page.wait_for_timeout(random.randint(1500, 3000))
        # Try contact page first
        links = await page.query_selector_all("a[href]")
        contact_url = None
        for link in links:
            href = await link.get_attribute("href") or ""
            if "contact" in href.lower():
                contact_url = href if href.startswith("http") else url.rstrip("/") + "/" + href.lstrip("/")
                break
        if contact_url:
            await page.goto(contact_url, timeout=20000)
            await page.wait_for_timeout(1500)
        text = await page.content()
        emails = re.findall(EMAIL_REGEX, text)
        # Filter junk
        emails = [e for e in emails if not any(x in e.lower() for x in ["example", "domain", "sentry", "wix", "googleapis"])]
        return emails[0] if emails else ""
    except Exception:
        return ""

async def main():
    rows = []
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.route("**/*.{css,png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}", lambda r: r.abort())
        page = await context.new_page()

        for i, row in enumerate(rows):
            if row.get("Email"):
                continue
            url = row.get("Website URL", "")
            if not url or not url.startswith("http"):
                continue
            email = await extract_email(page, url)
            row["Email"] = email
            status = f"✓ {email}" if email else "✗ none"
            print(f"[{i+1}/{len(rows)}] {row['Venue Name']} → {status}")
            # Progressive save every 10 rows
            if i % 10 == 0:
                with open(INPUT_FILE, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["Venue Name", "Website URL", "City", "Email"])
                    writer.writeheader()
                    writer.writerows(rows)
            time.sleep(random.uniform(2, 4))

        await browser.close()

    with open(INPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Venue Name", "Website URL", "City", "Email"])
        writer.writeheader()
        writer.writerows(rows)

    found = sum(1 for r in rows if r.get("Email"))
    print(f"\nDone. {found}/{len(rows)} emails found.")

if __name__ == "__main__":
    asyncio.run(main())