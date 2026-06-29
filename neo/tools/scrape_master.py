
"""
neo/tools/scrape_master.py
==========================
Multi-Directory OSINT Scraper (HereComesTheGuide, TheKnot, WeddingWire).
Bot Evasion: Native Chromium Argument Masking Active.
RAM Constraint: 8GB Optimized (Headless, CSS/Image/Font block).
"""
import csv
import re
from playwright.sync_api import sync_playwright
from neo.tools.content_validator import validate_pricing_doc, validate_pricing_text, rank_candidates

OUTPUT_FILE = "ohio_venues.csv"
DIRECTORIES = [
    "https://www.herecomestheguide.com/wedding-venues/ohio",
    "https://www.theknot.com/marketplace/wedding-reception-venues-ohio",
    "https://www.weddingwire.com/c/oh-ohio/wedding-venues/11-sca.html"
]

def block_bloat(route):
    """Intercept and abort non-essential payloads to conserve RAM."""
    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
        route.abort()
    else:
        route.continue_()

def execute_scrape():
    print("🕷️ [OSINT SPIDER] Deploying multi-directory stealth crawler...")
    master_data = {} 
    
    with sync_playwright() as p:
        # Native evasion arguments to bypass basic bot-sentinels
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
        )
        context = browser.new_context()
        
        # Mask webdriver variable
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()
        
        page.route("**/*", block_bloat)
        
        for directory in DIRECTORIES:
            print(f"\n📂 [TARGET DIRECTORY] {directory}")
            venue_links = set()
            current_url = directory
            
            for page_num in range(1, 4):
                try:
                    print(f"   -> Scanning directory page {page_num}...")
                    page.goto(current_url, timeout=45000)
                    page.wait_for_timeout(2000)
                    
                    for _ in range(3):
                        page.mouse.wheel(0, 1500)
                        page.wait_for_timeout(500)
                        
                    anchors = page.query_selector_all("a")
                    for a in anchors:
                        href = a.get_attribute("href")
                        if not href: continue
                        
                        clean_href = href.split("?")[0]
                        if "herecomestheguide.com" in directory and "/wedding-venues/ohio/" in clean_href:
                            venue_links.add(href if href.startswith("http") else f"https://www.herecomestheguide.com{href}")
                        elif "theknot.com" in directory and "/marketplace/" in clean_href and "-oh" in clean_href:
                            venue_links.add(href if href.startswith("http") else f"https://www.theknot.com{href}")
                        elif "weddingwire.com" in directory and "/biz/" in clean_href:
                            venue_links.add(href if href.startswith("http") else f"https://www.weddingwire.com{href}")
                            
                    if "herecomestheguide" in directory or "theknot" in directory:
                        current_url = f"{directory}?page={page_num + 1}"
                    else:
                        current_url = f"{directory.replace('.html', '')}-page{page_num + 1}.html"
                        
                except Exception as e:
                    print(f"   ⚠️ Pagination break: {str(e)}")
                    break
                    
            print(f"🎯 Acquired {len(venue_links)} nodes from {directory}. Commencing deep extraction...")
            
            for index, link in enumerate(list(venue_links)):
                if link == directory: continue
                print(f"   -> [{index+1}/{len(venue_links)}] Extracting: {link}")
                try:
                    page.goto(link, timeout=30000)
                    page.wait_for_timeout(1000)
                    
                    name_el = page.query_selector("h1")
                    name = name_el.inner_text().strip() if name_el else "Unknown Venue"
                    contact = None
                    
                    # TIER 1: mailto
                    for a in page.query_selector_all("a[href^='mailto:']"):
                        href = a.get_attribute("href")
                        if href:
                            extracted = href.replace("mailto:", "").split("?")[0].strip()
                            if not any(domain in extracted for domain in ["herecomestheguide", "theknot", "weddingwire"]):
                                contact = extracted
                                break
                    
                    # TIER 2: regex
                    if not contact:
                        content = page.content()
                        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                        valid_emails = [
                            e for e in emails 
                            if not e.endswith(("png", "jpg", "jpeg", "svg", "webp")) 
                            and not any(d in e for d in ["herecomestheguide", "theknot", "weddingwire", "sentry", "wix"])
                        ]
                        if valid_emails:
                            contact = valid_emails[0]
                            
                    # TIER 3: fallback url
                    if not contact:
                        for a in page.query_selector_all("a"):
                            href = a.get_attribute("href")
                            text = a.inner_text().lower()
                            if href and href.startswith("http") and ("website" in text or "visit" in text):
                                if not any(d in href for d in ["herecomestheguide", "theknot", "weddingwire", "facebook", "instagram", "twitter"]):
                                    contact = href
                                    break
                                    
                    if not contact:
                        contact = "No Contact Found"
                        
                    master_data[name] = contact
                    
                except Exception as e:
                    print(f"   ❌ Extraction failed: {str(e)}")
                    continue
                    
        browser.close()
        
    print(f"\n⚙️ Consolidating data and dropping duplicates...")
    final_rows = []
    seen_contacts = set()
    
    for name, contact in master_data.items():
        if contact != "No Contact Found" and contact not in seen_contacts:
            seen_contacts.add(contact)
            final_rows.append({"Venue_Name": name, "Email": contact})
            
    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Venue_Name", "Email"])
        writer.writeheader()
        writer.writerows(final_rows)
        
    print(f"✅ [MISSION COMPLETE] {len(final_rows)} unique venues written to {OUTPUT_FILE}.")

if __name__ == "__main__":
    execute_scrape()
