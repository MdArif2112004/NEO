"""
ca_pricing_harvester.py v2
Merges: california_venues.csv + ca_sent_log.csv + CA_Venues_Volume_Run.csv
For each venue: use URL if present, else DuckDuckGo search by name.
Extracts pricing text + PDFs. Keeps ALL venues (Yes + No) in output.
"""
import asyncio, csv, random, re
from pathlib import Path
from urllib.parse import quote_plus
from playwright.async_api import async_playwright

INPUT_FILES = ["california_venues.csv", "ca_sent_log.csv",
               "CA_Venues_Volume_Run.csv"]
OUTPUT_FILE = "ca_pricing_delivery.csv"
PDF_DIR     = Path("downloads/pdfs/ca_pricing")
PDF_DIR.mkdir(parents=True, exist_ok=True)
SAVE_EVERY  = 25

HEADERS = ["Venue Name","City","Website","Pricing Found",
           "Pricing Text","PDF File","Source"]

PRICE_KEYWORDS = ["pricing","packages","rates","investment","cost",
                  "wedding","events","celebrations","weddings",
                  "plan-your-event","plan-your-wedding","brochure"]
PRICE_REGEX    = (r"\$[\d,]+(?:\.\d{2})?(?:\s*[-–to]+\s*\$[\d,]+)?"
                  r"|\d+\s*(?:per person|pp|/person|guests?)")
SKIP_DOMAINS   = ["yelp.","theknot.","weddingwire.","yellowpages.",
                  "facebook.","instagram.","pinterest.","tripadvisor.",
                  "wikipedia.","youtube.","google.","duckduckgo."]

# ── Merge inputs, dedupe by name ───────────────────────────────
def load_merged():
    merged = {}  # name_lower -> {name, website, city}
    for fname in INPUT_FILES:
        if not Path(fname).exists():
            print(f"  (skip — {fname} not found)")
            continue
        with open(fname, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                name = (row.get("Venue Name") or "").strip()
                if not name:
                    continue
                key = name.lower()
                website = (row.get("Website URL") or "").strip()
                city    = (row.get("City") or "").strip()
                if key not in merged:
                    merged[key] = {"name": name, "website": website, "city": city}
                else:
                    # Fill gaps from later files
                    if not merged[key]["website"] and website:
                        merged[key]["website"] = website
                    if not merged[key]["city"] and city:
                        merged[key]["city"] = city
    return list(merged.values())

def load_done():
    if not Path(OUTPUT_FILE).exists():
        return set()
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        return {r["Venue Name"].strip().lower() for r in csv.DictReader(f)}

def save_rows(rows):
    if not rows:
        return
    for attempt in range(5):
        try:
            exists = Path(OUTPUT_FILE).exists()
            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if not exists:
                    w.writerow(HEADERS)
                w.writerows(rows)
            print(f"  💾 +{len(rows)} saved")
            return
        except PermissionError:
            print(f"  ⚠️ Close {OUTPUT_FILE} in Excel! Retry {attempt+1}/5")
            import time; time.sleep(8)

def extract_prices(text):
    hits = re.findall(PRICE_REGEX, text, re.IGNORECASE)
    seen, out = set(), []
    for h in hits:
        h = h.strip()
        if h and h not in seen:
            seen.add(h); out.append(h)
    return " | ".join(out[:15])

def is_real_site(url):
    return url.startswith("http") and not any(d in url.lower() for d in SKIP_DOMAINS)

# ── DuckDuckGo fallback: find venue site by name ───────────────
async def ddg_find_site(page, name, city):
    query = quote_plus(f"{name} {city} wedding venue official site")
    url = f"https://html.duckduckgo.com/html/?q={query}"
    try:
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await page.wait_for_timeout(random.randint(800, 1500))
        results = await page.query_selector_all("a.result__a, a.result__url")
        for r in results:
            href = await r.get_attribute("href") or ""
            # DDG wraps URLs — extract real target
            m = re.search(r"uddg=([^&]+)", href)
            if m:
                from urllib.parse import unquote
                href = unquote(m.group(1))
            if is_real_site(href):
                return href
    except:
        pass
    return ""

async def download_pdf(page, pdf_url, venue_name):
    try:
        safe  = re.sub(r"[^\w\-]", "_", venue_name)[:40]
        out   = PDF_DIR / f"{safe}.pdf"
        resp  = await page.context.request.get(pdf_url, timeout=15000)
        if resp.ok:
            out.write_bytes(await resp.body())
            return str(out)
    except:
        pass
    return ""

async def harvest(page, ddg_page, venue):
    name    = venue["name"]
    city    = venue["city"]
    website = venue["website"]

    # If no usable website → DDG search by name
    if not is_real_site(website):
        website = await ddg_find_site(ddg_page, name, city)
        await asyncio.sleep(random.uniform(1, 2))

    if not is_real_site(website):
        return [name, city, "", "No", "", "", "no-site-found"]

    pricing_text, pdf_file, source = "", "", "Web"
    try:
        await page.goto(website, timeout=15000, wait_until="domcontentloaded")
        await page.wait_for_timeout(random.randint(800, 1500))

        links       = await page.query_selector_all("a[href]")
        pricing_url = None
        pdf_links   = []
        for lnk in links:
            href = await lnk.get_attribute("href") or ""
            low  = href.lower()
            if low.endswith(".pdf"):
                full = href if href.startswith("http") \
                    else website.rstrip("/")+"/"+href.lstrip("/")
                pdf_links.append(full)
            elif any(k in low for k in PRICE_KEYWORDS) and not pricing_url:
                pricing_url = href if href.startswith("http") \
                    else website.rstrip("/")+"/"+href.lstrip("/")

        if pdf_links:
            pdf_file = await download_pdf(page, pdf_links[0], name)

        if pricing_url:
            try:
                await page.goto(pricing_url, timeout=12000,
                                wait_until="domcontentloaded")
                await page.wait_for_timeout(800)
                if not pdf_file:
                    for lnk in await page.query_selector_all("a[href$='.pdf']"):
                        h = await lnk.get_attribute("href") or ""
                        full = h if h.startswith("http") \
                            else pricing_url.rstrip("/")+"/"+h.lstrip("/")
                        pdf_file = await download_pdf(page, full, name)
                        if pdf_file:
                            break
            except:
                pass

        pricing_text = extract_prices(await page.inner_text("body"))
    except:
        pass

    found = "Yes" if (pricing_text or pdf_file) else "No"
    return [name, city, website, found, pricing_text, pdf_file, source]

async def main():
    venues = load_merged()
    done   = load_done()
    todo   = [v for v in venues if v["name"].lower() not in done]

    print(f"Merged unique venues: {len(venues)} | Done: {len(done)} | "
          f"To process: {len(todo)}\n")

    rows, hits = [], 0
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"))
        await ctx.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico,css}",
            lambda r: r.abort())
        page     = await ctx.new_page()
        ddg_page = await ctx.new_page()

        for i, v in enumerate(todo):
            row = await harvest(page, ddg_page, v)
            rows.append(row)
            if row[3] == "Yes":
                hits += 1
            mark = "💰" if row[3] == "Yes" else "·"
            print(f"[{i+1}/{len(todo)}] {mark} {row[0]} | "
                  f"{(row[4][:35] or 'no pricing')}{' +PDF' if row[5] else ''}")
            if len(rows) % SAVE_EVERY == 0:
                save_rows(rows[-SAVE_EVERY:])
            await asyncio.sleep(random.uniform(1.5, 2.5))

        await browser.close()

    rem = len(rows) % SAVE_EVERY
    if rem:
        save_rows(rows[-rem:])

    print(f"\n✅ Done. {hits}/{len(todo)} venues yielded pricing or PDF.")
    print(f"   → {OUTPUT_FILE} | PDFs → {PDF_DIR}")

if __name__ == "__main__":
    asyncio.run(main())