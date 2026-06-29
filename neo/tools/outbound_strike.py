"""
neo/tools/outbound_strike.py
============================
Cold Outbound SMTP Execution Engine.
Reads targets.csv, authenticates via Gmail SMTP, and executes highly-targeted
B2B pitches with randomized human-mimicry throttling.
RAM Constraint: 8GB Optimized (Iterative processing).
"""
import os
import csv
import time
import random
import smtplib
from email.message import EmailMessage

# Configuration matrix
TARGET_FILE = "targets.csv"
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

def create_payload(first_name):
    """Generates the hard-coded predatory pitch."""
    return (
        f"Hi {first_name},\n\n"
        "Most agencies and ecommerce brands are bleeding hours on manual data entry, "
        "scraping lead lists, or fixing broken API webhooks.\n\n"
        "I operate a custom, locally-hosted AI terminal architecture engineered for "
        "terminal-velocity data extraction. I don't do manual labor; I pipe your target "
        "directories, messy CSVs, or broken SaaS pipelines through a machine-precision execution loop.\n\n"
        "I work on flat rates ($30-$60 per bulk task), and I deliver in minutes, not days.\n\n"
        "Send me a sample 10-row dataset or a target URL you need scraped. I will run a "
        "free proof-of-concept for you right now."
    )

def execute_strike():
    print("\n⚙️ [OUTBOUND STRIKE] Initializing SMTP pipeline...")
    
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        print("❌ [SYSTEM FAULT] GMAIL_USER or GMAIL_APP_PASSWORD environment variables missing.")
        return

    if not os.path.exists(TARGET_FILE):
        print(f"❌ [SYSTEM FAULT] '{TARGET_FILE}' not found. Ensure targets are loaded.")
        return

    # Load targets into memory
    targets = []
    with open(TARGET_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            first_name = row.get("First Name", "Founder").strip()
            email = row.get("Email", "").strip()
            if email:
                targets.append({"name": first_name, "email": email})

    total_targets = len(targets)
    if total_targets == 0:
        print("⚠️ [SYSTEM FAULT] Target list is empty. Aborting strike.")
        return

    print(f"📡 [SMTP CONNECTED] Target array loaded: {total_targets} contacts.")
    
    for index, target in enumerate(targets):
        email_address = target["email"]
        first_name = target["name"]
        
        # Construct the email packet
        msg = EmailMessage()
        msg.set_content(create_payload(first_name))
        msg["Subject"] = "Automating your data extraction & API webhooks"
        msg["From"] = GMAIL_USER
        msg["To"] = email_address

        print(f"🎯 [{index + 1}/{total_targets}] Striking target: {email_address} ({first_name})...")
        
        try:
            # Initialize fresh connection per strike to bypass idle timeouts
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ [HIT] Payload delivered to {email_address}.")
            
        except Exception as e:
            print(f"❌ [FAULT] Delivery failed for {email_address}: {str(e)}")

        # Enforce Throttling Matrix (Unless it is the final target)
        if index < total_targets - 1:
            cooldown = random.randint(30, 90)
            print(f"⏳ [THROTTLE] Evading filters. Next strike in {cooldown} seconds...\n")
            time.sleep(cooldown)

    print("\n✅ [MISSION COMPLETE] Outbound strike array exhausted.")

if __name__ == "__main__":
    execute_strike()
