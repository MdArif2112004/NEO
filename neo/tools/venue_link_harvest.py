import requests
from bs4 import BeautifulSoup
from pathlib import Path
import time
import json
import re
from neo.tools.content_validator import validate_pricing_doc, validate_pricing_text

WEBSITE_LINKS = [
    "https://willowhavenlodge.com/",
    "https://gatheringsonthegreen.com/weddings",
    "https://22acresfarm.com/",
]

GDRIVE_LINKS = [
    "https://drive.google.com/file/d/1uvPYERVe0QLWLTmMQkspiJnZdQpjYq25/view?usp=drive_link",
    "https://drive.google.com/file/d/1oDj_bxsT6sPlMYqEhHrk6C1O1kqDwcBl/view?usp=drive_link",
    "https://drive.google.com/file/d/1guBLlq_FB63I0pHa2_cXI1PrQhfDvbZw/view?usp=sharing",
]

SAVE_DIR = Path("downloads/pdfs")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
results = []


def gdrive_direct(view_url):
    """Convert a Google Drive view URL to a direct download URL."""
    match = re.search(r"/file/d/([^/]+)", view_url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}", match.group(1)
    return None, None


# --- Google Drive PDFs ---
for gurl in GDRIVE_LINKS:
    direct, file_id = gdrive_direct(gurl)
    if not direct:
        print(f"✗ Could not parse Drive URL: {gurl}")
        continue
    try:
        session = requests.Session()
        r = session.get(direct, headers=headers, stream=True, timeout=30)
        # Handle Google's virus-scan confirmation page for large files
        if "text/html" in r.headers.get("Content-Type", ""):
            token_match = re.search(r'confirm=([0-9A-Za-z_-]+)', r.text)
            if token_match:
                confirm = token_match.group(1)
                r = session.get(direct + f"&confirm={confirm}", headers=headers, stream=True, timeout=30)
        if not validate_pricing_doc(r.content, file_id or ""):
            print(f"✗ GDrive PDF {file_id} failed validation — skipping")
            continue
        fname = f"gdrive_{file_id}.pdf"
        with open(SAVE_DIR / fname, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        print(f"✓ GDrive PDF: {fname}")
        results.append({"url": gurl, "type": "pdf", "file": str(SAVE_DIR / fname)})
    except Exception as e:
        print(f"✗ {gurl} — {e}")
    time.sleep(2)


# --- Venue websites ---
for base_url in WEBSITE_LINKS:
    try:
        r = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        # 1. Find direct PDF links on the page
        pdf_links = [
            a["href"] for a in soup.find_all("a", href=True)
            if ".pdf" in a["href"].lower()
        ]

        for pdf_url in pdf_links:
            if not pdf_url.startswith("http"):
                pdf_url = base_url.rstrip("/") + "/" + pdf_url.lstrip("/")
            pr = requests.get(pdf_url, headers=headers, stream=True, timeout=15)
            if not validate_pricing_doc(pr.content, base_url.split("//")[1].split("/")[0]):
                print(f"✗ PDF {pdf_url} failed validation — skipping")
                continue
            fname = pdf_url.split("/")[-1].split("?")[0]
            with open(SAVE_DIR / fname, "wb") as f:
                for chunk in pr.iter_content(8192):
                    f.write(chunk)
            print(f"✓ PDF: {fname}")
            results.append({"url": base_url, "type": "pdf", "file": fname})

        # 2. If no PDF, extract pricing text (keyword scrape)
        if not pdf_links:
            text = soup.get_text(separator=" ", strip=True)
            if not validate_pricing_text(text, base_url.split("//")[1].split("/")[0]):
                print(f"✗ Text from {base_url} failed validation — skipping")
                continue
            price_lines = [
                line.strip() for line in text.splitlines()
                if any(k in line.lower() for k in ["$", "pricing", "package", "rate", "cost", "starting"])
            ]
            summary = " | ".join(price_lines[:5])
            print(f"✓ Text: {base_url} → {summary[:120]}")
            results.append({"url": base_url, "type": "text", "data": summary})

        time.sleep(3)

    except Exception as e:
        print(f"✗ {base_url} — {e}")


# Save all results
out = Path("downloads/venue_text_pricing.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nDone. Results → {out}")
