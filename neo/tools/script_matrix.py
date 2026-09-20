"""
neo/tools/script_matrix.py
==========================
Phase 2: The Retention Scriptwriter.
Reads raw trending JSON data and uses Groq (Llama-3) to write highly engaging, 
retention-optimized 60-second video scripts.
"""
import os
import json
from groq import Groq

def generate_arbitrage_scripts(input_json="trending.json", output_dir="scripts") -> str:
    """Reads trending topics and generates high-retention video scripts via Groq."""
    if not os.path.exists(input_json):
        return f"❌ SCRIPT FAULT: Could not find '{input_json}'. Run OSINT scraper first."
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "❌ SCRIPT FAULT: GROQ_API_KEY is missing from environment variables."

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with open(input_json, 'r', encoding='utf-8') as f:
            trending_data = json.load(f)
    except Exception as e:
        return f"❌ SCRIPT FAULT: Failed to read {input_json}: {str(e)}"

    if not trending_data:
        return "❌ SCRIPT FAULT: No data inside trending.json."

    client = Groq(api_key=api_key)
    success_count = 0
    
    print("\n[SCRIPTWRITER] Synthesizing raw data into retention scripts...")

    # We will just process the top 3 stories to save API limits during this test
    for i, topic in enumerate(trending_data[:3]):
        title = topic.get("title", "Unknown")
        body = topic.get("body", "")
        
        print(f"  -> Writing script for: {title[:40]}...")
        
        system_prompt = """You are a master short-form video scriptwriter (TikTok/YouTube Shorts).
        Your goal is to maximize Average View Duration (AVD).
        Follow this strict pacing:
        1. THE HOOK (0-3s): Open with a shocking, controversial, or highly curious statement related to the topic. Do not introduce yourself.
        2. THE MEAT (3-45s): Explain the core of the story simply. Use short, punchy sentences.
        3. THE LOOP/CALL TO ACTION (45-60s): End with a question or statement that naturally encourages viewers to re-watch or comment.
        
        OUTPUT FORMAT: Return ONLY the spoken text of the script. Do not include visual cues, bracketed text, or speaker labels. Just the words to be spoken.
        Keep it under 150 words total."""
        
        user_prompt = f"Topic Title: {title}\nContext: {body}\n\nWrite the script."

        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            script_text = response.choices[0].message.content.strip()
            
            # Save the script
            filename = f"script_{i+1}_{title[:20].replace(' ', '_').replace('/', '_')}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(script_text)
                
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to write script {i+1}: {str(e)}")
            
    return f"✅ SCRIPT GENERATION COMPLETE: {success_count} viral scripts saved to '{output_dir}/' folder."
