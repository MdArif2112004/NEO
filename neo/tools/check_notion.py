"""
neo/tools/check_notion.py
=========================
N.E.O. Connection Diagnostic: Identifies target Notion Database metadata.
RAM Constraint: 8GB Optimized (Lightweight standard request loop).
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

def inspect_database():
    print("📡 [N.E.O. DIAGNOSTIC] Pinging Notion API Matrix...")
    if not NOTION_TOKEN or not DATABASE_ID:
        print("❌ [SYSTEM FAULT] Missing NOTION_API_KEY or NOTION_DATABASE_ID in .env file.")
        return

    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            
            # Extract plain text title from Notion structure
            title_list = data.get("title", [])
            title = title_list[0].get("plain_text", "Untitled Database") if title_list else "Untitled Database"
            
            # Extract column names (properties)
            properties = list(data.get("properties", {}).keys())
            
            print("\n================ SYSTEM LINK SECURED ================")
            print(f"🎯 DATABASE NAME : {title}")
            print(f"🆔 DATABASE ID   : {DATABASE_ID}")
            print(f"📊 LIVE COLUMNS  : {', '.join(properties)}")
            print("=====================================================")
            print("✅ Connection verified. Target CRM is live and fully exposed.")
        else:
            print(f"❌ [API REFUSAL] Status {response.status_code}: Verification failed.")
            print(f"💡 Detail: {response.text}")
    except Exception as e:
        print(f"❌ [CRITICAL FAULT] Diagnostics aborted: {str(e)}")

if __name__ == "__main__":
    inspect_database()