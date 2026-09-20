"""
neo/tools/pdf_extractor.py
==========================
[SHADOW EXTRACTION] - Bulk PDF Acquisition Node.
RAM Constraint: 8GB Optimized (Streaming chunks, zero memory bloat).
"""
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# The secure vault for extracted payloads
LOOT_DIR = "loot/wedding_assets"

def execute_shadow_extraction(target_url):
    print(f"📡 [N.E.O. RECON] Scanning matrix at: {target_url}...")
    
    if not os.path.exists(LOOT_DIR):
        os.makedirs(LOOT_DIR)
        
    try:
        # Penetrate the target URL
        response = requests.get(target_url, timeout=15)
        response.raise_for_status()
        
        # Parse the HTML matrix
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a')
        
        pdf_links = []
        for link in links:
            href = link.get('href')
            if href and '.pdf' in href.lower():
                # Reconstruct full URL if the link is relative
                full_url = urljoin(target_url, href)
                if full_url not in pdf_links:
                    pdf_links.append(full_url)
                    
        if not pdf_links:
            print("⚠️ [SYSTEM ALERT] Zero PDF nodes detected on target surface.")
            return
            
        print(f"🎯 [TARGETS LOCKED] {len(pdf_links)} PDF documents found. Initiating extraction...")
        
        # Pull each payload
        for url in pdf_links:
            # Clean the filename from the URL
            filename = url.split('/')[-1]
            if '?' in filename:
                filename = filename.split('?')[0]
            if not filename.endswith('.pdf'):
                filename = "extracted_document.pdf"
                
            filepath = os.path.join(LOOT_DIR, filename)
            
            print(f"   -> Pulling payload: {filename}...")
            
            # Stream the download to strictly enforce the 8GB RAM constraint
            with requests.get(url, stream=True, timeout=20) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
        print(f"\n✅ [MISSION COMPLETE] All assets secured in neo_core/{LOOT_DIR}.")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ [CRITICAL FAULT] Network connection rejected: {e}")

if __name__ == "__main__":
    # TARGET OVERRIDE REQUIRED HERE
    TARGET_SURFACE = "YOUR_URL_HERE" 
    
    if TARGET_SURFACE == "YOUR_URL_HERE":
        print("❌ [SYSTEM FAULT] Target surface not defined.")
        print("💡 Open pdf_extractor.py and inject the target URL at the bottom of the script.")
    else:
        execute_shadow_extraction(TARGET_SURFACE)