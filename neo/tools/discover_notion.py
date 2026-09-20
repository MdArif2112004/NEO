"""
neo/tools/discover_notion.py
============================
N.E.O. Target Node Discovery: Scans and extracts shared Database IDs.
RAM Constraint: 8GB Optimized (Lightweight stateless network call).
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_API_KEY")

def discover_databases():
    print("📡 [N.E.O. SEARCH] Scanning shared workspace for database nodes...")
    if not NOTION_TOKEN:
        print("❌ [SYSTEM FAULT] NOTION_API_KEY missing from .env workspace.")
        return

    url = "https://api.notion.com/v1/search"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    # Force the API to filter strictly for structured databases, ignoring standard text pages
    payload = {
        "filter": {"property": "object", "value": "database"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            results = response.json().get("results", [])
            if not results:
                print("⚠️ [SYSTEM ALERT] Zero databases detected.")
                print("💡 Ensure you have explicitly added the 'N.E.O. Database Bridge' connection inside a Table database page.")
                return

            print("\n================ DISCOVERED TARGET NODES ================")
            for db in results:
                title_list = db.get("title", [])
                title = title_list[0].get("plain_text", "Untitled Table") if title_list else "Untitled Table"
                # Strip dashes out to clean the ID for the .env matrix
                db_id = db.get("id").replace("-", "")
                print(f"🎯 TARGET NAME : {title}")
                print(f"🆔 TRUE DB ID  : {db_id}")
                print("---------------------------------------------------------")
            print("=========================================================")
        else:
            print(f"❌ [API REFUSAL] Status {response.status_code}")
            print(f"Detail: {response.text}")
    except Exception as e:
        print(f"❌ [CRITICAL FAULT] Discovery sequence collapsed: {str(e)}")

if __name__ == "__main__":
    discover_databases()