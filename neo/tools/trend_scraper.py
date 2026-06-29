"""
neo/tools/trend_scraper.py
==========================
Phase 1: OSINT Topic Scraper (Hacker News Variant).
Bypasses Reddit's Cloudflare wall by pivoting to the open Hacker News Firebase API.
"""
import json
import requests

def scrape_trending_topics(output_file="trending_data.json") -> str:
    """Extracts the top trending tech/startup stories directly from Hacker News API."""
    extracted_data = []
    
    # HN Firebase API is 100% open and free. No keys required.
    top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    item_url_base = "https://hacker-news.firebaseio.com/v0/item/{}.json"

    print("\n[OSINT] Initiating Hacker News API Extraction...")

    try:
        # Get the IDs of the top trending stories right now
        response = requests.get(top_stories_url, timeout=10)
        if response.status_code != 200:
            return f"❌ OSINT FAULT: Failed to connect to Hacker News API."
            
        story_ids = response.json()[:15] # Grab the top 15 trending topics
        
        for story_id in story_ids:
            try:
                # Fetch the specific details for each story
                story_resp = requests.get(item_url_base.format(story_id), timeout=10)
                if story_resp.status_code == 200:
                    story_data = story_resp.json()
                    
                    # We want engaging stories, preferably with text or high discussion
                    if not story_data: continue
                    
                    title = story_data.get('title', '')
                    text = story_data.get('text', '') # HN text posts
                    url = story_data.get('url', '')   # HN link posts
                    score = story_data.get('score', 0)
                    
                    # Combine text and URL for the LLM to write the video script from
                    body_content = f"{text}\nSource: {url}"
                    
                    extracted_data.append({
                        "niche": "technews",
                        "title": title,
                        "body": body_content[:2000], 
                        "score": score
                    })
                    print(f"  -> Extracted: {title[:50]}...")
                    
            except Exception as e:
                print(f"  ❌ Failed to extract story {story_id}: {str(e)}")

    except Exception as e:
        return f"❌ OSINT FAULT: Connection crash: {str(e)}"

    if not extracted_data:
        return "❌ OSINT FAULT: No valid threads found."

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4)
        return f"✅ OSINT SCRAPE COMPLETE: {len(extracted_data)} trending HN threads saved to {output_file}."
    except Exception as e:
        return f"❌ OSINT FAULT: Could not write JSON: {str(e)}"
