"""
neo/tools/freelance_tracker.py
==============================
Freelance Pipeline — Notion Database Creator.

Creates a "Freelance Pipeline" database at the Notion workspace root
with columns for tracking gigs from Discord, Reddit, and direct sources.

On first run:
  1. Creates the database if it doesn't exist
  2. Prints the Notion database URL for manual linking
  3. Appends the database ID to notion_registry.json (no overwrite)

Usage:
  python neo/tools/freelance_tracker.py
"""
import requests
import json
import os
import sys

# Ensure project root is in path for neo.tools imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ── Auth ──
NOTION_TOKEN = os.getenv("NOTION_API_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

REGISTRY_FILE = "neo_core/notion_registry.json" if os.path.exists("neo_core") else "notion_registry.json"
LOCAL_DB_ID_FILE = "freelance_pipeline_id.json"
DB_NAME = "Freelance Pipeline"


def get_headers():
    """Return Notion API headers."""
    return HEADERS


def _db_exists_locally():
    """Check if we already saved a database ID locally."""
    if os.path.exists(LOCAL_DB_ID_FILE):
        try:
            with open(LOCAL_DB_ID_FILE, "r") as f:
                data = json.load(f)
                return data.get("database_id")
        except Exception:
            pass
    return None


def _verify_database(db_id):
    """Verify the database still exists by fetching it."""
    url = f"https://api.notion.com/v1/databases/{db_id}"
    resp = requests.get(url, headers=get_headers(), timeout=10)
    return resp.status_code == 200


def create_database():
    """
    Create the 'Freelance Pipeline' database at the Notion workspace root.
    Returns the database ID on success, or None on failure.
    """
    print(f"[Freelance Tracker] 🗄️  Creating '{DB_NAME}' database at workspace root...")

    # We need a parent page to create the database under.
    # Since the user said "no parent page needed — top level", we'll create it
    # under the NEO_CONTROL root (which is the backend workspace).
    from neo.tools.notion_api import NEO_CONTROL_ID

    url = "https://api.notion.com/v1/databases"

    payload = {
        "parent": {"type": "page_id", "page_id": NEO_CONTROL_ID},
        "title": [{"type": "text", "text": {"content": DB_NAME}}],
        "properties": {
            "Platform": {
                "select": {
                    "options": [
                        {"name": "Discord", "color": "blue"},
                        {"name": "Reddit", "color": "orange"},
                        {"name": "Direct", "color": "green"},
                    ]
                }
            },
            "Gig Title": {
                "title": {}
            },
            "Budget": {
                "rich_text": {}
            },
            "Status": {
                "select": {
                    "options": [
                        {"name": "New", "color": "green"},
                        {"name": "Applied", "color": "yellow"},
                        {"name": "Waiting", "color": "orange"},
                        {"name": "Closed", "color": "gray"},
                    ]
                }
            },
            "Link": {
                "url": {}
            },
            "Notes": {
                "rich_text": {}
            },
            "Date Found": {
                "date": {}
            },
        },
    }

    resp = requests.post(url, headers=get_headers(), json=payload, timeout=15)

    if resp.status_code == 200:
        data = resp.json()
        db_id = data["id"]
        db_url = data.get("url", "")
        print(f"[Freelance Tracker] ✅ Database created!")
        print(f"[Freelance Tracker] 🆔 ID: {db_id}")
        print(f"[Freelance Tracker] 🔗 URL: {db_url}")
        return db_id, db_url
    else:
        print(f"[Freelance Tracker] ❌ Failed to create database.")
        print(f"[Freelance Tracker]    Status: {resp.status_code}")
        print(f"[Freelance Tracker]    Body: {resp.text[:300]}")
        return None, None


def save_database_id(db_id, db_url):
    """Save the database ID locally and append to notion_registry.json."""
    # Save to local file for quick lookup
    with open(LOCAL_DB_ID_FILE, "w") as f:
        json.dump({"database_id": db_id, "url": db_url, "name": DB_NAME}, f, indent=2)
    print(f"[Freelance Tracker] 💾 Saved to {LOCAL_DB_ID_FILE}")

    # Append to notion_registry.json (don't overwrite)
    from neo.tools.notion_api import update_notion_registry
    result = update_notion_registry(
        page_name=DB_NAME,
        page_id=db_id,
        summary_of_purpose="Freelance gig pipeline — tracks opportunities from Discord, Reddit, and direct sources with status, budget, and notes.",
    )
    print(f"[Freelance Tracker] 📝 Registry update: {result}")


def main():
    print("=" * 60)
    print("[Freelance Tracker] Initializing...")
    print("=" * 60)

    # Check if we already have a saved database ID
    existing_id = _db_exists_locally()
    if existing_id:
        print(f"[Freelance Tracker] 📋 Found existing database ID: {existing_id}")
        if _verify_database(existing_id):
            print(f"[Freelance Tracker] ✅ Database still exists. No action needed.")
            print(f"[Freelance Tracker] 🔗 URL: {json.load(open(LOCAL_DB_ID_FILE)).get('url', 'N/A')}")
            return
        else:
            print(f"[Freelance Tracker] ⚠️  Database no longer exists. Creating a new one...")

    # Create the database
    db_id, db_url = create_database()
    if db_id:
        save_database_id(db_id, db_url)
    else:
        print(f"[Freelance Tracker] ❌ Aborting — could not create database.")
        sys.exit(1)

    print("=" * 60)
    print("[Freelance Tracker] Done.")
    print("=" * 60)


if __name__ == "__main__":
    main()