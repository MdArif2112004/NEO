"""
neo/tools/notion_pipeline.py
============================
N.E.O. Module: Dirty CSV to Notion Integration.
RAM Constraint: 8GB Optimized (Pandas vectorization).
"""
import os
import pandas as pd
from notion_client import Client
from dotenv import load_dotenv

load_dotenv(override=True)

NOTION_TOKEN = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
CSV_FILE = "raw_leads.csv"

def sanitize_payload(file_path):
    print(f"⚙️ [N.E.O. INGESTION] Reading raw payload from {file_path}...")
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"❌ [SYSTEM FAULT] '{file_path}' missing. Create it in the root directory.")
        return None

    print(f"📊 Raw rows loaded: {len(df)}")
    df.columns = df.columns.str.strip().str.lower()
    
    if 'name' not in df.columns or 'email' not in df.columns:
        print("❌ [SYSTEM FAULT] CSV must contain 'Name' and 'Email' columns.")
        return None

    print("🧹 [N.E.O. SANITIZER] Executing data vectorization...")
    df['email'] = df['email'].astype(str).str.strip().str.lower()
    df['email'] = df['email'].replace(['nan', 'none', ''], pd.NA)
    df.dropna(subset=['email'], inplace=True)
    
    df['name'] = df['name'].astype(str).str.strip().str.title()
    df['name'] = df['name'].replace(['Nan', 'None', ''], 'Unknown Name')

    print(f"✅ Sanitization complete. Valid rows remaining: {len(df)}")
    return df

def deploy_to_notion(df):
    if df is None or df.empty:
        print("⚠️ [WARNING] No valid data to deploy.")
        return
        
    print("📡 [N.E.O. DEPLOYMENT] Initiating Notion API uplink...")
    notion = Client(auth=NOTION_TOKEN)
    success_count = 0
    
    for index, row in df.iterrows():
        name = row['name']
        email = row['email']
        print(f"   -> Pushing to database: {name} | {email}")
        
        try:
            new_page = {
                "parent": {"database_id": DATABASE_ID},
                "properties": {
                    "Name": {"title": [{"text": {"content": name}}]},
                    "Email": {"email": email},
                    "Status": {"status": {"name": "Not started"}}
                }
            }
            notion.pages.create(**new_page)
            success_count += 1
        except Exception as e:
            print(f"   ❌ [FAULT] Failed to push {name}: {str(e)}")

    print(f"\n✅ [MISSION COMPLETE] {success_count}/{len(df)} leads successfully deployed to Notion.")

def execute_pipeline():
    clean_dataframe = sanitize_payload(CSV_FILE)
    if clean_dataframe is not None:
        deploy_to_notion(clean_dataframe)

if __name__ == "__main__":
    execute_pipeline()