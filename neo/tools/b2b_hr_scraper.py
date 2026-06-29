"""
b2b_hr_scraper.py — Clutch.co Name + Location Collector (paginated)
====================================================================
Collects Company Name + Location across multiple Clutch listing pages.
Does NOT visit profile pages — Clutch paywalls website URLs, so the
enricher (b2b_enrich.py) resolves websites + emails via DuckDuckGo instead.

Over-extract strategy: grab 150 names, enrich all, filter to 50 perfect rows.

Output: B2B_HR_Raw.csv  (Company Name, Website[blank], Location, Email[blank])

Dependencies: playwright
Install: pip install playwright && playwright install chromium
Run:
  python neo/tools/b2b_hr_scraper.py
  python neo/tools/b2b_hr_scraper.py https://clutch.co/hr 150

If Cloudflare blocks: set HEADLESS = False below and retry.
"""

import sys
import csv
import time
import random
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ── Config ─────────────────────────────────────────────────────────────────────

TARGET_URL  = sys.argv[1] if len(sys.argv) > 1 else "https://clutch.co/hr"
MAX_RESULTS = int(sys.argv[2]) if len(sys.argv) > 2 else 150
OUTPUT      = Path("B2B_HR_Raw.csv")
HEADLESS    = True
MAX_PAGES   = 6           # safety cap; stops early when a page adds nothing
DELAY       = (2, 4)

CARD_SEL     = "li.provider-row, .provider-list-item, article.provider, .directory-list__item"
NAME_SEL     = "h3.company-name, .company_info__name h3, .provider-info__company-name, h3 a"
LOCATION_SEL = ".locality, .provider-info__location, [class*='location']"

def cloudflare_blocked(title: str, content: str) -> bool:
    sig = ("just a moment", "attention required", "cloudflare", "403 forbidden",
           "access denied", "enable javascript and cookies")
    return any(s in (title + content).lower() for s in sig)

def scrape():
    records, seen = [], set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=HEADLESS,
            args=["--disable-blink-features=AutomationControlled",
                  "--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/125.0.0.0 Safari/537.36"),
        )
        page = ctx.new_page()
        page.route("**/*", lambda r: r.abort()
                   if r.request.resource_type in ("image", "stylesheet", "font", "media")
                   else r.continue_())

        sep = "&" if "?" in TARGET_URL else "?"
        for page_num in range(MAX_PAGES):
            url = TARGET_URL if page_num == 0 else f"{TARGET_URL}{sep}page={page_num}"
            print(f"[page {page_num+1}] {url}")
            try:
                page.goto(url, wait_until="networkidle", timeout=30_000)
            except PWTimeout:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)

            title, content = page.title(), page.content()[:1500].lower()
            if cloudflare_blocked(title, content):
                print("\n⛔ Cloudflare blocked. Set HEADLESS=False and retry,")
                print("   or switch directory (upcity.com / bark.com).")
                break

            try:
                page.wait_for_selector(CARD_SEL, timeout=12_000)
            except PWTimeout:
                print("   No company cards found — stopping.")
                break

            cards = page.query_selector_all(CARD_SEL)
            new_count = 0
            for card in cards:
                name = loc = ""
                try:
                    n = card.query_selector(NAME_SEL)
                    name = n.inner_text().strip() if n else ""
                except Exception:
                    pass
                try:
                    l = card.query_selector(LOCATION_SEL)
                    loc = l.inner_text().strip() if l else ""
                except Exception:
                    pass
                if name and name not in seen:
                    seen.add(name)
                    records.append({"name": name, "loc": loc})
                    new_count += 1

            print(f"   +{new_count} new (total {len(records)})")
            if new_count == 0:
                print("   No new companies — stopping pagination.")
                break
            if len(records) >= MAX_RESULTS:
                break
            time.sleep(random.uniform(*DELAY))

        browser.close()
    return records[:MAX_RESULTS]

def main():
    print("=" * 56)
    print(f"  NEO B2B Collector | target={TARGET_URL} | want={MAX_RESULTS}")
    print("=" * 56 + "\n")

    records = scrape()

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Company Name", "Website", "Location", "Email"])
        for r in records:
            w.writerow([r["name"], "", r["loc"], ""])

    print(f"\n✅ {len(records)} companies -> {OUTPUT.resolve()}")
    print("   Next: python neo/tools/b2b_enrich.py")

if __name__ == "__main__":
    main()
