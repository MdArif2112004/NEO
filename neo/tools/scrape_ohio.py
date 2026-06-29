"""
neo/tools/scrape_ohio.py
========================
Headless OSINT Scraper: Ohio Wedding Venues (Deep Crawl).
RAM Constraint: 8GB Optimized. 
Patch: Footer-Email Bypass & 'mailto:' Priority Active.
"""
import csv
import re
from playwright.sync_api import sync_playwright

TARGET_URL = "https://www.herecomestheguide.com/wedding-venues/ohio"
OUTPUT_FILE = "ohio_venues.csv"

def block_bloat(route):
    """Intercepts and aborts non-essential network payloads to save RAM."""
    if route.request.resource_type in ["image", "stylesheet", "font", "media"]:
        route.abort()
    else:
        route.continue_()

def execute_scrape():
    print(f"🕷️ Deploying headless crawler to {TARGET_URL}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Enable network interception
        page.route("**/*", block_bloat)
        
        try:
            page.goto(TARGET_URL, timeout=60000)
            page.wait_for_timeout(2000)
            print("✅ Directory loaded. Acquiring venue nodes...")
            
            # Extract venue profile links
            venue_links = []
            for a in page.query_selector_all("a"):
                href = a.get_attribute("href")
                if href and "/wedding-venues/" in href and href != TARGET_URL:
                    full_url = href if href.startswith("http") else f"https://www.herecomestheguide.com{href}"
                    if full_url not in venue_links:
                        venue_links.append(full_url)
            
            print(f"🎯 {len(venue_links)} venues found. Commencing deep extraction...")

            # Initialize CSV and write row-by-row
            with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["Venue_Name", "Email"])
                writer.writeheader()
                
                for index, link in enumerate(venue_links):
                    print(f"   -> [{index+1}/{len(venue_links)}] Scanning {link}...")
                    try:
                        page.goto(link, timeout=30000)
                        
                        name_el = page.query_selector("h1")
                        venue_name = name_el.inner_text().strip() if name_el else "Unknown Venue"
                        
                        contact = "No Email Found"
                        
                        # METHOD 1: Priority extraction via mailto tags
                        for a in page.query_selector_all("a[href^='mailto:']"):
                            href = a.get_attribute("href")
                            if href:
                                extracted = href.replace("mailto:", "").split("?")[0].strip()
                                # Blacklist the directory's own email
                                if "herecomestheguide.com" not in extracted:
                                    contact = extracted
                                    break
                                    
                        # METHOD 2: Fallback to Regex if mailto is obfuscated
                        if contact == "No Email Found":
                            content = page.content()
                            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                            
                            # Filter false positives and the global directory email
                            valid_emails = [
                                e for e in emails 
                                if not e.endswith(("png", "jpg", "jpeg", "webp")) 
                                and "herecomestheguide.com" not in e
                            ]
                            if valid_emails:
                                contact = valid_emails[0]
                        
                        writer.writerow({"Venue_Name": venue_name, "Email": contact})
                        
                    except Exception as e:
                        print(f"   ❌ Failed to scan {link}: {str(e)}")
                        continue

            print(f"\n✅ Extraction complete. Payload written to {OUTPUT_FILE}.")

        except Exception as e:
            print(f"❌ Critical Scraper Fault: {str(e)}")
        finally:
            browser.close()

if __name__ == "__main__":
    execute_scrape()
