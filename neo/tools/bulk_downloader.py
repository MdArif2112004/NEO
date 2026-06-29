"""
neo/tools/bulk_downloader.py
============================
N.E.O. Regex Extraction Node: Parses raw text for URLs and sorts payloads.
RAM Constraint: 8GB Optimized (Streaming chunks, regex vectorization).
"""
import os
import re
import requests

# Directories and Targets
SOURCE_FILE = "email_dump.txt"
LOOT_DIR = "loot/wedding_assets"
MANUAL_REVIEW_FILE = "loot/manual_website_links.txt"

def execute_extraction():
    print(f"📡 [N.E.O. RECON] Scanning {SOURCE_FILE} for target URLs...")
    
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ [SYSTEM FAULT] {SOURCE_FILE} not found. Please create it and paste your email text.")
        return

    os.makedirs(LOOT_DIR, exist_ok=True)
    
    # Read the raw text dump
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Regex to find all http/https links
    url_pattern = re.compile(r'(https?://[^\s>"\']+)')
    found_urls = url_pattern.findall(raw_text)
    
    # Clean trailing punctuation from URLs (like commas or periods)
    cleaned_urls = list(set([url.rstrip('.,;)') for url in found_urls]))

    if not cleaned_urls:
        print("⚠️ [SYSTEM ALERT] Zero URLs detected in the text dump.")
        return

    print(f"🎯 [TARGETS LOCKED] {len(cleaned_urls)} total URLs extracted.")
    
    pdf_links = []
    website_links = []
    
    # Sort the payloads
    for url in cleaned_urls:
        if '.pdf' in url.lower():
            pdf_links.append(url)
        else:
            website_links.append(url)

    # 1. Isolate the website links for manual review
    if website_links:
        with open(MANUAL_REVIEW_FILE, "w", encoding="utf-8") as f:
            for link in website_links:
                f.write(link + "\n")
        print(f"📂 Logged {len(website_links)} non-PDF portal links to {MANUAL_REVIEW_FILE}")

    # 2. Download the direct PDFs
    if pdf_links:
        print(f"⬇️ Initiating automated extraction of {len(pdf_links)} PDF targets...")
        for url in pdf_links:
            filename = url.split('/')[-1].split('?')[0]
            if not filename.endswith('.pdf'):
                filename = f"extracted_{pdf_links.index(url)}.pdf"
                
            filepath = os.path.join(LOOT_DIR, filename)
            print(f"   -> Pulling: {filename}...")
            
            try:
                with requests.get(url, stream=True, timeout=20) as r:
                    r.raise_for_status()
                    with open(filepath, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
            except Exception as e:
                print(f"   ❌ [FAULT] Could not secure {filename}: {e}")
                
    print("\n✅ [MISSION COMPLETE] Extraction cycle terminated.")

if __name__ == "__main__":
    execute_extraction()