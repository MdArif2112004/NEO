"""
neo/tools/notion_api.py
=======================
The Oracle Architect with Local Registry (RAG).
Handles two root nodes: ARIF OS (Frontend) and NEO CONTROL (Backend).
"""
import requests
import json
import os
import datetime

# --- PASTE YOUR SECRET KEY HERE ---
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "") 
# ----------------------------------

# Your specific Notion Page IDs
ARIF_OS_ID = "327a328b385a8142bcb3cd0b160736d1"
NEO_CONTROL_ID = "36aa328b385a807b9f90cbd92fb21868"

REGISTRY_FILE = "neo_core/notion_registry.json" if os.path.exists("neo_core") else "notion_registry.json"

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def read_notion_registry(query: str = "") -> str:
    """Reads the local map. If a query is provided, it searches for specific pages."""
    if not os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump({"ARIF_OS_ROOT": {"id": ARIF_OS_ID, "purpose": "Frontend Root"}, 
                       "NEO_CONTROL_ROOT": {"id": NEO_CONTROL_ID, "purpose": "Backend Root"}}, f, indent=2)
        return "Registry initialized."
        
    try:
        with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # If no query is provided, but the map is huge, force Neo to use a query
        if not query and len(data) > 15:
            return "❌ The registry is too large to load all at once. Please use read_notion_registry(query='your_search_term') to find what you need."
            
        # If a query is provided, filter the results!
        if query:
            results = {}
            for name, info in data.items():
                if query.lower() in name.lower() or query.lower() in info.get("purpose", "").lower():
                    results[name] = info
            return json.dumps(results, indent=2) if results else f"📭 No pages found in registry matching '{query}'."
            
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"❌ Error reading registry: {e}"

def update_notion_registry(page_name: str, page_id: str, summary_of_purpose: str) -> str:
    """Saves a newly created page to the local map so Neo remembers what it is for."""
    data = {}
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
            
    data[page_name] = {"id": page_id, "purpose": summary_of_purpose}
    
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    return f"✅ Registered '{page_name}' into the local map."

def create_notion_page(title: str, is_frontend: bool = True, parent_id: str = None) -> str:
    """Creates a new page. If is_frontend is True, builds in ARIF OS. If False, builds in NEO CONTROL."""
    url = "https://api.notion.com/v1/pages"
    
    if parent_id and parent_id.lower() != "none":
        parent = parent_id
    else:
        parent = ARIF_OS_ID if is_frontend else NEO_CONTROL_ID
        
    data = {
        "parent": {"page_id": parent},
        "properties": {"title": [{"text": {"content": title}}]}
    }
    
    try:
        res = requests.post(url, headers=HEADERS, json=data)
        if res.status_code == 200:
            new_id = res.json()["id"]
            return f"✅ Created Notion Page: '{title}'. ID: {new_id}. NOTE: Use update_notion_registry to save this ID and its purpose!"
        else:
            return f"❌ Error from Notion: {res.text}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

def write_notion_content(page_id: str, text: str, block_type: str = "paragraph") -> str:
    """Writes content (paragraph, h1, h2, h3, todo, bullet) inside a specific Notion page."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    
    valid_types = {"paragraph": "paragraph", "h1": "heading_1", "h2": "heading_2", "h3": "heading_3", "todo": "to_do", "bullet": "bulleted_list_item"}
    notion_type = valid_types.get(block_type.lower(), "paragraph")
    
    data = {
        "children": [
            {"object": "block", "type": notion_type, notion_type: {"rich_text": [{"type": "text", "text": {"content": text}}]}}
        ]
    }
    try:
        res = requests.patch(url, headers=HEADERS, json=data)
        return f"✅ Added '{block_type}' to page {page_id}." if res.status_code == 200 else f"❌ Error: {res.text}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

def read_notion_page(page_id: str) -> str:
    """Reads the complete text blocks of a specific Notion page, no matter how long it is."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code != 200: 
            return f"❌ Error reading Notion: {res.text}"
            
        blocks = res.json().get("results", [])
        if not blocks: 
            return "📭 This page is currently empty."
            
        content_log = []
        
        # Look through every single block and extract the text
        for block in blocks:
            b_type = block["type"]
            if b_type in block and "rich_text" in block[b_type]:
                text_arr = block[b_type]["rich_text"]
                if text_arr: 
                    # Combine all text segments in the block
                    full_text = "".join([t["plain_text"] for t in text_arr])
                    content_log.append(f"[{b_type.upper()}] {full_text}")
                    
        return f"📄 Complete Content of Page {page_id}:\n" + "\n".join(content_log)
    except Exception as e:
        return f"❌ Connection Error: {e}"

def create_calendar_task(task_name: str, days_from_now: int, database_id: str) -> str:
    """Creates a calendar task. days_from_now: 0 for today, 1 for tomorrow, etc."""
    url = "https://api.notion.com/v1/pages"
    
    # Automatically calculates the exact future date!
    target_date = (datetime.datetime.now() + datetime.timedelta(days=int(days_from_now))).date().isoformat()
    
    data = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": task_name}}]
            },
            "Date": {
                "date": {"start": target_date}
            }
        }
    }
    
    try:
        res = requests.post(url, headers=HEADERS, json=data)
        if res.status_code == 200:
            return f"✅ Scheduled '{task_name}' for {target_date}."
        else:
            return f"❌ Error from Notion: {res.text}"
    except Exception as e:
        return f"❌ Connection Error: {e}"

def insert_notion_db_row(database_id: str, company_name: str, data_dict: dict) -> str:
    """
    Inserts a new row into a Notion Database.
    'data_dict' should be a dictionary of other columns (e.g., {"Pricing": "$19/mo", "Feature": "AI Bot"}).
    """
    url = "https://api.notion.com/v1/pages"
    
    # In Notion, the primary column is usually called "Name" and is a "title" type.
    properties = {
        "Name": {
            "title": [{"text": {"content": company_name}}]
        }
    }
    
    # Convert the rest of the dictionary into standard Notion text columns
    for key, value in data_dict.items():
        properties[key] = {
            "rich_text": [{"text": {"content": str(value)}}]
        }
            
    data = {
        "parent": {"type": "database_id", "database_id": database_id},
        "properties": properties
    }

    try:
        res = requests.post(url, headers=HEADERS, json=data)
        if res.status_code == 200:
            return f"✅ Row for '{company_name}' successfully added to Notion Database."
        else:
            return f"❌ Notion API Error: {res.text}"
    except Exception as e:
        return f"❌ Connection Error: {e}"


import csv

import csv

def push_csv_to_notion(csv_filepath: str, target_page_id: str) -> str:
    """
    Fully Autonomous Ingestion.
    Reads a local CSV, creates a BRAND NEW Notion Database inside the target page,
    dynamically generates the columns based on the CSV headers, and populates the data.
    """
    if not os.path.exists(csv_filepath):
        return f"❌ NOTION FAULT: File '{csv_filepath}' does not exist."
        
    try:
        with open(csv_filepath, mode='r', encoding='utf-8-sig') as f:
            reader = list(csv.DictReader(f))
            if not reader:
                return "❌ NOTION FAULT: CSV is empty or missing headers."
            
            headers_list = list(reader[0].keys())
            
        # --- 1. DYNAMICALLY CREATE THE DATABASE ARCHITECTURE ---
        db_url = "https://api.notion.com/v1/databases"
        
        # The first column is always the 'title' property in Notion
        title_prop = headers_list[0]
        
        properties_schema = {
            title_prop: {"title": {}}
        }
        
        # All other columns are dynamically generated as rich_text properties
        for header in headers_list[1:]:
            properties_schema[header] = {"rich_text": {}}
            
        db_payload = {
            "parent": {"type": "page_id", "page_id": target_page_id},
            "title": [{"type": "text", "text": {"content": f"Extracted Data: {os.path.basename(csv_filepath)}"}}],
            "properties": properties_schema
        }
        
        res_db = requests.post(db_url, headers=HEADERS, json=db_payload)
        if res_db.status_code != 200:
            return f"❌ NOTION DB CREATION FAULT: {res_db.text}"
            
        new_db_id = res_db.json()["id"]
        
        # --- 2. POPULATE THE NEW DATABASE ---
        success_count = 0
        row_url = "https://api.notion.com/v1/pages"
        
        for row in reader:
            row_props = {
                title_prop: {
                    "title": [{"text": {"content": str(row.get(title_prop, ""))[:2000]}}]
                }
            }
            for header in headers_list[1:]:
                row_props[header] = {
                    "rich_text": [{"text": {"content": str(row.get(header, ""))[:2000]}}]
                }
                
            row_payload = {
                "parent": {"database_id": new_db_id},
                "properties": row_props
            }
            
            res_row = requests.post(row_url, headers=HEADERS, json=row_payload)
            if res_row.status_code == 200:
                success_count += 1
                
        return f"✅ AUTONOMOUS BRIDGE COMPLETE: Built new database and pushed {success_count} rows."
        
    except Exception as e:
        return f"❌ AUTONOMOUS PARSING FAULT: {str(e)}"
