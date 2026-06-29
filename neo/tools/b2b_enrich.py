"""
b2b_enrich.py v3 — Website + Email enrichment
===============================================
Primary  : SerpApi (free 250/mo, no card, real Google results)
Fallback : Bing scrape (zero setup, works at low volume)

Setup (free, 2 min):
  1. serpapi.com -> sign up free -> Dashboard -> copy API key
  2. Add to .env:  SERPAPI_KEY=your_key
  If key absent -> auto-falls back to Bing scrape.

Reads:  B2B_HR_Raw.csv
Writes: B2B_HR_Leads_Enriched.csv
Run:    python neo/tools/b2b_enrich.py
"""

import os, re, csv, time, random, urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

INPUT_CSV  = Path("B2B_HR_Raw.csv")
OUTPUT_CSV = Path("B2B_HR_Leads_Enriched.csv")

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
USE_SERP    = bool(SERPAPI_KEY)

DELAY_SEARCH = (1, 2) if USE_SERP else (4, 7)
DELAY_SITE   = (1, 2)

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/125.0.0.0 Safari/537.36"),
    "Accept-Language": "en-US,en;q=0.9",
}

SKIP_DOMAINS = {
    "clutch.co","duckduckgo.com","bing.com","google.com","serpapi.com",
    "linkedin.com","facebook.com","twitter.com","instagram.com",
    "yelp.com","yellowpages.com","youtube.com","crunchbase.com",
    "glassdoor.com","indeed.com","wikipedia.org","goodfirms.co",
    "zoominfo.com","apollo.io","rocketreach.co","owler.com",
}

# ── Email helpers ──────────────────────────────────────────────────────────────

EMAIL_RE    = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
VERSION_RE  = re.compile(r"@[\d]+\.[\d]")          # npm: package@1.2.3
CSS_RE      = re.compile(r"@\d+\.\.")               # css: wght@100..900
JUNK_LOCAL  = {"noreply","no-reply","donotreply","support","help","privacy","legal",
               "abuse","security","webmaster","postmaster","sentry","mailer","bounce",
               "unsubscribe","billing","payments","notifications","alerts","admin",
               "spam","report","feedback","newsletter","careers","jobs","example"}
JUNK_EXT    = {"png","jpg","jpeg","gif","svg","js","css","woff","ttf","eot","ico",
               "webp","mp4","pdf"}
JUNK_DOMAINS = {"example.com","domain.com","example.org","test.com","placeholder.com"}
PRIORITY    = ["founder","ceo","owner","director","partner","head","contact",
               "hello","team","info","sales","enqui","query"]

def best_email(html: str, site_domain: str = "") -> str:
    found = []
    for e in EMAIL_RE.findall(html):
        e = e.rstrip(".")                            # strip trailing dot
        local  = e.split("@")[0].lower()
        domain = e.split("@")[-1].lower()
        ext    = domain.split(".")[-1].lower()
        if VERSION_RE.search(e): continue            # npm package version
        if CSS_RE.search(e):     continue            # css font-weight value
        if ext in JUNK_EXT:      continue
        if domain in JUNK_DOMAINS: continue          # placeholder domains
        if any(j in local for j in JUNK_LOCAL): continue
        if len(e) > 80 or " " in e: continue
        # Reject if email domain clearly doesn't match the company site
        if site_domain and domain not in site_domain and site_domain not in domain:
            # Allow common cases: info@company vs company.com -> match on root name
            site_root  = site_domain.split(".")[0]
            email_root = domain.split(".")[0]
            if len(site_root) > 3 and len(email_root) > 3 and site_root != email_root:
                continue
        found.append(e)
    if not found:
        return ""
    for p in PRIORITY:
        for e in found:
            if p in e.lower():
                return e.lower()
    return found[0].lower()

def clean_domain(url: str) -> str:
    try:
        netloc = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")
        if netloc and "." in netloc and not any(s in netloc for s in SKIP_DOMAINS):
            return f"https://www.{netloc}"
    except Exception:
        pass
    return ""

# ── Website lookup ─────────────────────────────────────────────────────────────

def lookup_serpapi(name: str) -> str:
    """Real Google results via SerpApi — reliable, no bot-blocking."""
    try:
        r = requests.get(
            "https://serpapi.com/search",
            params={"q": f"{name} official website",
                    "api_key": SERPAPI_KEY,
                    "num": 5, "engine": "google"},
            timeout=15,
        )
        if r.status_code == 429:
            print("    ⚠️  SerpApi monthly quota hit (250/mo). Switching to Bing.")
            return lookup_bing(name)
        data = r.json()
        for item in data.get("organic_results", []):
            d = clean_domain(item.get("link", ""))
            if d:
                return d
    except Exception as e:
        print(f"    SerpApi error: {e}")
    return ""

def lookup_bing(name: str) -> str:
    """Bing HTML scrape — zero setup, works at low volume."""
    try:
        r = requests.get(
            "https://www.bing.com/search",
            params={"q": f"{name} official website"},
            headers=HEADERS, timeout=15,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select("li.b_algo h2 a"):
            d = clean_domain(a.get("href", ""))
            if d:
                return d
    except Exception as e:
        print(f"    Bing error: {e}")
    return ""

def lookup_website(name: str) -> str:
    return lookup_serpapi(name) if USE_SERP else lookup_bing(name)

# ── Email from site ────────────────────────────────────────────────────────────

def get_email(website: str) -> str:
    site_domain = website.replace("https://www.","").replace("http://www.","").split("/")[0].lower()
    for path in ("/contact", "/contact-us", "/about-us", "/about", ""):
        try:
            r = requests.get(
                website.rstrip("/") + path,
                headers=HEADERS, timeout=12, allow_redirects=True,
            )
            e = best_email(r.text, site_domain)
            if e:
                return e
        except Exception:
            pass
        time.sleep(random.uniform(*DELAY_SITE))
    return ""

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not INPUT_CSV.exists():
        print(f"Not found: {INPUT_CSV}. Run b2b_hr_scraper.py first.")
        return

    mode = f"SerpApi (reliable, {SERPAPI_KEY[:6]}...)" if USE_SERP else \
           "Bing scrape (no SERPAPI_KEY in .env — add one for best results)"
    print(f"Search: {mode}\n")

    rows = list(csv.DictReader(open(INPUT_CSV, encoding="utf-8")))
    total = len(rows)
    print(f"Enriching {total} companies...\n")
    print(f"{'#':<4} {'Company':<40} {'Website':<34} Email")
    print("-" * 100)

    sites = emails = 0

    for i, row in enumerate(rows, 1):
        name    = row.get("Company Name", "").strip()
        loc     = row.get("Location", "").strip()
        website = row.get("Website", "").strip()
        email   = row.get("Email", "").strip()

        if not website:
            website = lookup_website(name)
            time.sleep(random.uniform(*DELAY_SEARCH))

        if website and not email:
            email = get_email(website)
            time.sleep(random.uniform(*DELAY_SITE))

        sites  += 1 if website else 0
        emails += 1 if email else 0

        # Write row immediately — safe against crashes mid-run
        with open(OUTPUT_CSV, "w" if i == 1 else "a",
                  newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["Company Name","Website","Location","Email"])
            if i == 1:
                w.writeheader()
            w.writerow({"Company Name": name, "Website": website,
                        "Location": loc, "Email": email})

        status = email if email else "✗"
        print(f"{i:<4} {name[:38]:<40} {(website or '')[:32]:<34} {status}")

        # SerpApi quota warning
        if USE_SERP and i % 50 == 0:
            used = i
            remaining = 250 - used  # rough estimate
            print(f"\n  ℹ️  ~{remaining} SerpApi queries remaining this month.\n")

    print(f"\n{'='*60}")
    print(f"  Done   : {total} companies")
    print(f"  Sites  : {sites}/{total}")
    print(f"  Emails : {emails}/{total}  ({emails/total*100:.0f}% yield)")
    print(f"  Output : {OUTPUT_CSV.resolve()}")
    print(f"{'='*60}")
    print("\n  Next: python neo/tools/b2b_sanitize.py 50")

if __name__ == "__main__":
    main()
