"""
ca_venue_volume_scraper.py v3
Primary: Yellow Pages (fixed selectors)
"""
import asyncio, csv, random, re
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE   = "CA_Venues_Volume_Run.csv"
EMAIL_REGEX   = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
SAVE_INTERVAL = 50
JUNK_DOMAINS  = ["sentry","wix","example","domain","googleapis",
                 "schema","adobe","png","jpg","svg","gif","yelp","yp.com",
                 "yellowpages","w3.org","openstreetmap"]
HEADERS       = ["Venue Name","Website URL","City","Email","Source"]

CA_CITIES = [
    "Los Angeles CA","San Francisco CA","San Diego CA","Sacramento CA",
    "San Jose CA","Oakland CA","Santa Barbara CA","Napa CA",
    "Palm Springs CA","Monterey CA","Carmel CA","Malibu CA",
    "Pasadena CA","Temecula CA","Santa Cruz CA","Sonoma CA",
    "Newport Beach CA","Laguna Beach CA","Long Beach CA","Ventura CA",
    "Santa Rosa CA","San Luis Obispo CA","Santa Monica CA",
    "Thousand Oaks CA","Riverside CA","Anaheim CA","Irvine CA",
    "Fresno CA","Modesto CA","Bakersfield CA","Chico CA",
    "Stockton CA","Visalia CA","Oxnard CA","Redding CA"
]

def load_seen():
    if not Path(OUTPUT_FILE).exists():
        return set()
    with open(OUTPUT_FILE,"r",encoding="utf-8") as f:
        return {r[0].strip().lower() for r in csv.reader(f) if r}

def save_rows(rows):
    if not rows:
        return
    # Close check — retry if file locked
    for attempt in range(5):
        try:
            exists = Path(OUTPUT_FILE).exists()
            with open(OUTPUT_FILE,"a",newline="",encoding="utf-8") as f:
                w = csv.writer(f)
                if not exists:
                    w.writerow(HEADERS)
                w.writerows(rows)
            count = sum(1 for _ in open(OUTPUT_FILE,encoding="utf-8")) - 1
            print(f"  💾 +{len(rows)} saved (file total: {count})")
            return
        except PermissionError:
            print(f"  ⚠️ CSV locked — close it in Excel! Retrying in 10s... ({attempt+1}/5)")
            import time; time.sleep(10)
    print("  ❌ Could not save — CSV still locked. Close Excel and re-run.")

def clean_email(e):
    return None if any(j in e.lower() for j in JUNK_DOMAINS) else e

def extract_email(html):
    found = re.findall(EMAIL_REGEX, html)
    cleaned = [e for e in found if clean_email(e)]
    return cleaned[0] if cleaned else ""

async def get_email(page, url):
    if not url or not url.startswith("http"):
        return ""
    try:
        await page.goto(url, timeout=12000, wait_until="domcontentloaded")
        await page.wait_for_timeout(700)
        links = await page.query_selector_all("a[href]")
        for lnk in links:
            href = (await lnk.get_attribute("href") or "").lower()
            if "contact" in href:
                contact = href if href.startswith("http") \
                    else url.rstrip("/")+"/"+href.lstrip("/")
                try:
                    await page.goto(contact, timeout=8000,
                                    wait_until="domcontentloaded")
                    await page.wait_for_timeout(500)
                except:
                    pass
                break
        return extract_email(await page.content())
    except:
        return ""

# ── Yellow Pages ───────────────────────────────────────────────
async def scrape_yp(sp, ep, city, seen):
    rows = []
    city_enc = city.replace(" ","+")

    for pg in range(1, 16):
        url = (f"https://www.yellowpages.com/search?"
               f"search_terms=wedding+venues&"
               f"geo_location_terms={city_enc}&page={pg}")
        try:
            await sp.goto(url, timeout=30000, wait_until="domcontentloaded")
            await sp.wait_for_timeout(random.randint(2000, 3500))

            # Dump all text to debug selector issues
            cards = await sp.query_selector_all(
                ".srp-listing, .result, [class*='listing'], "
                "[class*='organic'], .v-card")

            if not cards:
                # Try broader — get any business name links
                cards = await sp.query_selector_all("h2")

            if not cards:
                print(f"  YP {city} p{pg}: 0 cards")
                break

            page_hits = 0
            for card in cards:
                try:
                    # Multiple selector fallbacks for name
                    name = ""
                    for sel in [".business-name", ".n", "a.business-name",
                                 "[class*='business-name']", "a"]:
                        el = await card.query_selector(sel)
                        if el:
                            name = (await el.inner_text()).strip()
                            if name:
                                break

                    if not name or name.lower() in seen or len(name) < 3:
                        continue

                    # City
                    city_el = await card.query_selector(
                        ".locality, [class*='city'], address")
                    city_r = (await city_el.inner_text()).strip() \
                        if city_el else city.replace(" CA","")
                    city_r = city_r.split(",")[0].strip()

                    # Website — direct link or YP profile
                    website = ""
                    for sel in ["a.track-visit-website",
                                 "a[class*='website']",
                                 "a[href*='http'][rel='nofollow']"]:
                        web_el = await card.query_selector(sel)
                        if web_el:
                            website = await web_el.get_attribute("href") or ""
                            if website and "yellowpages" not in website:
                                break
                            website = ""

                    email = await get_email(ep, website)
                    seen.add(name.lower())
                    rows.append([name, website, city_r, email, "YellowPages"])
                    print(f"  ✓ {name} | {city_r} | {email or '—'}")
                    page_hits += 1

                    if len(rows) % SAVE_INTERVAL == 0:
                        save_rows(rows[-SAVE_INTERVAL:])

                    await asyncio.sleep(random.uniform(0.8, 1.5))

                except:
                    continue

            if page_hits == 0:
                print(f"  YP {city} p{pg}: parsed but 0 usable — stopping city")
                break

        except Exception as e:
            print(f"  YP {city} p{pg} err: {e}")
            break

        await asyncio.sleep(random.uniform(3, 5))

    return rows

# ── Yelp fallback ──────────────────────────────────────────────
async def scrape_yelp(sp, ep, city, seen):
    rows = []
    city_slug = city.replace(" CA","").replace(" ","+")

    for pg in range(3):
        url = (f"https://www.yelp.com/search?"
               f"find_desc=wedding+venues&"
               f"find_loc={city_slug}%2C+CA&start={pg*10}")
        try:
            await sp.goto(url, timeout=25000, wait_until="domcontentloaded")
            await sp.wait_for_timeout(random.randint(2500, 4000))

            links = await sp.query_selector_all("a[href*='/biz/']")
            biz = {}
            for lnk in links:
                href = await lnk.get_attribute("href") or ""
                text = (await lnk.inner_text()).strip()
                if "/biz/" in href and text and len(text) > 3 \
                        and "?" not in href.split("/biz/")[-1]:
                    full = f"https://www.yelp.com{href}" \
                        if href.startswith("/") else href
                    if full not in biz:
                        biz[full] = text.split("\n")[0].strip()

            if not biz:
                break

            for biz_url, name in list(biz.items())[:15]:
                if not name or name.lower() in seen:
                    continue
                website = ""
                try:
                    await sp.goto(biz_url, timeout=12000,
                                  wait_until="domcontentloaded")
                    await sp.wait_for_timeout(800)
                    for el in await sp.query_selector_all("a[href^='http']"):
                        h = await el.get_attribute("href") or ""
                        if "yelp.com" not in h and "facebook" not in h \
                                and h.startswith("http"):
                            website = h
                            break
                except:
                    pass

                email = await get_email(ep, website)
                seen.add(name.lower())
                city_r = city.replace(" CA","")
                rows.append([name, website, city_r, email, "Yelp"])
                print(f"  ✓ {name} | {city_r} | {email or '—'}")

                if len(rows) % SAVE_INTERVAL == 0:
                    save_rows(rows[-SAVE_INTERVAL:])

                await asyncio.sleep(random.uniform(1.5, 2.5))

        except Exception as e:
            print(f"  Yelp {city} p{pg} err: {e}")
            break

        await asyncio.sleep(random.uniform(3, 5))

    return rows

# ── Main ───────────────────────────────────────────────────────
async def main():
    seen     = load_seen()
    all_rows = []
    total    = 0
    print(f"Loaded {len(seen)} seen. Target: 1000+\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        ctx = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"),
            viewport={"width":1280,"height":800}
        )
        await ctx.route(
            "**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
            lambda r: r.abort())

        sp = await ctx.new_page()
        ep = await ctx.new_page()

        for city in CA_CITIES:
            if total >= 1200:
                print("✅ 1200 reached — done.")
                break
            print(f"\n── {city} (total: {total}) ──")

            rows = await scrape_yp(sp, ep, city, seen)

            if len(rows) < 3:
                print(f"  YP thin ({len(rows)}) → Yelp fallback...")
                rows += await scrape_yelp(sp, ep, city, seen)

            saved_count = (len(rows) // SAVE_INTERVAL) * SAVE_INTERVAL
            remainder   = rows[saved_count:]
            if remainder:
                save_rows(remainder)

            all_rows.extend(rows)
            total += len(rows)
            await asyncio.sleep(random.uniform(4, 7))

        await browser.close()

    print(f"\n✅ Run complete. {total} new venues added.")

if __name__ == "__main__":
    asyncio.run(main())