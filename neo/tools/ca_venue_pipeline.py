import argparse
import csv
import imaplib
import email
import os
import random
import re
import smtplib
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

SMTP_HOST = "smtp-relay.brevo.com"
SMTP_PORT = 587
IMAP_HOST = "imap-mail.outlook.com"
IMAP_PORT = 993

SENDER_EMAIL    = os.getenv("BURNER_EMAIL")
SENDER_PASSWORD = os.getenv("BURNER_EMAIL_PASSWORD")

VENUES_CSV      = "california_venues.csv"
SENT_LOG        = "ca_sent_log.csv"
REPLIES_CSV     = "ca_replies.csv"
DELIVERY_CSV    = "ca_delivery_sheet.csv"
ERRORS_LOG      = "ca_errors.txt"
PDF_DIR         = Path("downloads/pdfs/ca")
TEMPLATE_FILE   = "neo/tools/venue_email_template.txt"

PDF_DIR.mkdir(parents=True, exist_ok=True)

# ── helpers ──────────────────────────────────────────────────────────────────

def load_template():
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()

def load_venues():
    with open(VENUES_CSV, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def log_error(msg):
    with open(ERRORS_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} — {msg}\n")

def already_sent():
    if not Path(SENT_LOG).exists():
        return set()
    with open(SENT_LOG, "r", encoding="utf-8") as f:
        return {row["Email"] for row in csv.DictReader(f) if row.get("Email")}

def append_sent(venue_name, email_addr):
    exists = Path(SENT_LOG).exists()
    with open(SENT_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["Venue Name", "Email", "Timestamp"])
        w.writerow([venue_name, email_addr, datetime.now().isoformat()])

def append_delivery(venue_name, city, source, data):
    exists = Path(DELIVERY_CSV).exists()
    with open(DELIVERY_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not exists:
            w.writerow(["Venue Name", "City", "Source", "Extracted Pricing Data"])
        w.writerow([venue_name, city, source, data])

# ── stage 1 ───────────────────────────────────────────────────────────────────

def stage1():
    print("=== STAGE 1: EMAIL BLAST ===")
    template = load_template()
    venues   = load_venues()
    sent     = already_sent()

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for v in venues:
            addr = v.get("Email", "").strip()
            name = v.get("Venue Name", "").strip()
            if not addr or addr in sent:
                continue
            body    = template.replace("[Venue Name]", name)
            subject = f"Free Listing for {name} — Venue Discovery Platform"
            msg = MIMEText(body, "plain")
            msg["From"]    = SENDER_EMAIL
            msg["To"]      = addr
            msg["Subject"] = subject
            try:
                server.sendmail(SENDER_EMAIL, addr, msg.as_string())
                append_sent(name, addr)
                print(f"✓ Sent → {name} ({addr})")
            except Exception as e:
                log_error(f"Send failed {addr}: {e}")
                print(f"✗ Failed → {addr}")
            time.sleep(random.uniform(45, 90))

    print("Stage 1 complete.")

# ── stage 2 ───────────────────────────────────────────────────────────────────

def strip_html(html):
    return re.sub(r"<[^>]+>", " ", html)

def extract_prices(text):
    hits = re.findall(r"\$[\d,]+(?:\s*[-–]\s*\$[\d,]+)?|\d+\s*per\s+\w+", text)
    return " | ".join(hits[:10]) if hits else ""

def extract_links(text):
    urls = re.findall(r"https?://\S+", text)
    return [u for u in urls if any(k in u.lower() for k in
            ["pricing", "packages", "rates", "investment", "cost"])]

def stage2():
    print("=== STAGE 2: REPLY HARVEST ===")
    venues  = load_venues()
    domains = {v.get("Email", "").split("@")[-1].lower() for v in venues if v.get("Email")}

    with open(REPLIES_CSV, "a", newline="", encoding="utf-8") as rf:
        writer = csv.writer(rf)
        if Path(REPLIES_CSV).stat().st_size == 0:
            writer.writerow(["Venue Name", "Type", "Data"])

        with imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT) as mail:
            mail.login(SENDER_EMAIL, SENDER_PASSWORD)
            mail.select("INBOX")
            since = (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
            _, ids = mail.search(None, f'(SINCE {since})')

            for uid in ids[0].split():
                try:
                    _, data = mail.fetch(uid, "(RFC822)")
                    msg     = email.message_from_bytes(data[0][1])
                    sender  = msg.get("From", "")
                    domain  = re.search(r"@([\w.]+)", sender)
                    domain  = domain.group(1).lower() if domain else ""

                    if domain not in domains:
                        continue

                    venue_name = next(
                        (v["Venue Name"] for v in venues
                         if v.get("Email", "").split("@")[-1].lower() == domain), domain)

                    body_text = ""
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "text/plain":
                            body_text += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        elif ct == "text/html":
                            body_text += strip_html(
                                part.get_payload(decode=True).decode("utf-8", errors="ignore"))
                        elif ct == "application/pdf":
                            fname = part.get_filename() or f"{domain}_{uid.decode()}.pdf"
                            out   = PDF_DIR / fname
                            out.write_bytes(part.get_payload(decode=True))
                            writer.writerow([venue_name, "PDF", str(out)])
                            append_delivery(venue_name, "", "Email PDF", str(out))
                            print(f"✓ PDF saved: {fname}")

                    prices = extract_prices(body_text)
                    links  = extract_links(body_text)

                    if prices:
                        writer.writerow([venue_name, "Text Pricing", prices])
                        append_delivery(venue_name, "", "Email Text", prices)
                        print(f"✓ Pricing text: {venue_name}")
                    for lnk in links:
                        writer.writerow([venue_name, "Pricing Link", lnk])
                        append_delivery(venue_name, "", "Email Link", lnk)
                        print(f"✓ Pricing link: {venue_name}")

                except Exception as e:
                    log_error(f"IMAP parse error uid {uid}: {e}")

    print("Stage 2 complete.")

# ── stage 3 ───────────────────────────────────────────────────────────────────

def stage3():
    import asyncio
    from playwright.async_api import async_playwright

    print("=== STAGE 3: WEB FALLBACK ===")
    venues = load_venues()

    replied = set()
    if Path(REPLIES_CSV).exists():
        with open(REPLIES_CSV, "r", encoding="utf-8") as f:
            replied = {row["Venue Name"] for row in csv.DictReader(f)}

    targets = [v for v in venues if v["Venue Name"] not in replied and v.get("Website URL")]
    print(f"{len(targets)} venues with no reply — running web fallback.")

    async def harvest(venue):
        name = venue["Venue Name"]
        url  = venue["Website URL"]
        city = venue.get("City", "")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            await context.route(
                "**/*.{css,png,jpg,jpeg,gif,svg,woff,woff2,ttf,ico}",
                lambda r: r.abort())
            page = await context.new_page()
            try:
                await page.goto(url, timeout=20000)
                links = await page.query_selector_all("a[href]")
                pricing_url = None
                for lnk in links:
                    href = await lnk.get_attribute("href") or ""
                    if any(k in href.lower() for k in
                           ["pricing", "packages", "rates", "investment", "cost"]):
                        pricing_url = href if href.startswith("http") \
                            else url.rstrip("/") + "/" + href.lstrip("/")
                        break
                if pricing_url:
                    await page.goto(pricing_url, timeout=20000)
                text    = await page.inner_text("body")
                prices  = extract_prices(text)
                result  = prices if prices else "No public pricing"
                source  = pricing_url or url
                append_delivery(name, city, f"Web: {source}", result)
                print(f"✓ Web: {name} → {result[:60]}")
            except Exception as e:
                log_error(f"Web fallback {name}: {e}")
                print(f"✗ Web failed: {name}")
            finally:
                await browser.close()

    for v in targets:
        asyncio.run(harvest(v))
        time.sleep(random.uniform(2, 4))

    print("Stage 3 complete.")

# ── entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, choices=[1, 2, 3], required=True)
    args = parser.parse_args()
    if args.stage == 1:
        stage1()
    elif args.stage == 2:
        stage2()
    elif args.stage == 3:
        stage3()