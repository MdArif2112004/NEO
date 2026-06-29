"""
neo/tools/blast_venues.py
=========================
Cold Outbound SMTP Execution Engine (Ghost Protocol Node).
Sends via existing Gmail, routes replies to Outlook.
"""
import os
import csv
import time
import random
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

TARGET_FILE = "ohio_venues.csv"
GMAIL_USER = "thechosenoneytchannel@gmail.com"
OUTLOOK_INBOX = "arif.weddingplanning26@outlook.com" # Replies route here
GMAIL_APP_PASSWORD = os.environ.get("BURNER_GMAIL_APP_PASSWORD")

def execute_blast():
    print("\n⚙️ Initializing SMTP Ghost Protocol...")
    
    if not os.path.exists(TARGET_FILE):
        print(f"❌ '{TARGET_FILE}' not found.")
        return

    if not GMAIL_APP_PASSWORD:
        print("❌ [SYSTEM FAULT] BURNER_GMAIL_APP_PASSWORD missing from .env file.")
        return

    targets = []
    with open(TARGET_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("Email", "").strip()
            if "@" in email and not email.startswith("http"):
                targets.append(email)

    targets = list(set(targets))
    total_targets = len(targets)
    
    if total_targets == 0:
        print("⚠️ No valid email addresses found.")
        return

    print(f"📡 SMTP pipeline armed. Loaded {total_targets} unique venues.")
    print(f"🛡️ Engine: {GMAIL_USER} | Routing replies to: {OUTLOOK_INBOX}")
    
    payload = (
        "Hi there - I'm starting to plan my wedding for sometime in June 2028. "
        "We're expecting around 110 guests and I'd love to learn more about your venue. "
        "Would you be able to send over a pricing guide? We're in the early stages "
        "and just trying to get a sense of what's in our budget. Thank you!"
    )
    
    for index, email_address in enumerate(targets):
        msg = EmailMessage()
        msg.set_content(payload)
        msg["Subject"] = "Wedding Inquiry - June 2028"
        
        # GHOST PROTOCOL INJECTION
        # Spoofs display name and forces replies to the Outlook node
        msg["From"] = formataddr(("Arif - Wedding Planning", GMAIL_USER))
        msg["Reply-To"] = OUTLOOK_INBOX
        msg["To"] = email_address

        print(f"🎯 [{index + 1}/{total_targets}] Striking: {email_address}...")
        
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.send_message(msg)
            print(f"✅ Delivered.")
        except Exception as e:
            print(f"❌ Delivery failed for {email_address}: {str(e)}")

        if index < total_targets - 1:
            cooldown = random.randint(45, 90)
            print(f"⏳ Throttling to evade sentinels. Next strike in {cooldown} seconds...\n")
            time.sleep(cooldown)

    print("\n✅ Deployment exhausted. Mission complete.")

if __name__ == "__main__":
    execute_blast()
