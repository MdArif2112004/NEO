"""
neo/tools/clip_ingest.py
========================
Weapon: [CLIP INGEST]
Intercepts the OS clipboard, routes raw data through the Groq matrix 
for tactical structuring, and overwrites the clipboard with the payload.
Optimized for 8GB RAM local constraints.
"""
import os
import time
import pyperclip
from groq import Groq

def execute_clip_ingest(instruction: str = "Format and summarize this text concisely.") -> str:
    """Grabs clipboard text, processes it via LLM, and replaces the clipboard."""
    try:
        # Mechanical Patch: Bypass Windows Clipboard Lock (Error 5) via 3-strike loop
        raw_text = ""
        for _ in range(3):
            raw_text = pyperclip.paste()
            if raw_text and len(raw_text.strip()) > 0:
                break
            time.sleep(0.5)

        if not raw_text or len(raw_text.strip()) == 0:
            return "❌ INGEST FAULT: System clipboard is empty, locked by Windows OS, or contained non-text data."
            
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return "❌ INGEST FAULT: Missing GROQ_API_KEY in environment."
            
        print(f"\n[CLIP INGEST] Intercepting payload ({len(raw_text)} chars)...")
        client = Groq(api_key=api_key)
        
        system_prompt = (
            "You are N.E.O., a tactical data parser. "
            f"Directive: {instruction} "
            "Output ONLY the final processed text. Zero conversational filler. Zero markdown backticks."
        )
        
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        processed_payload = response.choices[0].message.content.strip()
        
        # Force write payload to clipboard with retry loop
        for _ in range(3):
            try:
                pyperclip.copy(processed_payload)
                break
            except:
                time.sleep(0.5)
        
        return f"✅ INGEST COMPLETE: Clipboard overwritten. Payload compressed ({len(raw_text)} -> {len(processed_payload)} chars)."
        
    except Exception as e:
        return f"❌ INGEST FAULT: Pipeline collapse: {str(e)}"

if __name__ == "__main__":
    import sys
    import io
    # Force Windows terminal to accept UTF-8 Emojis
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("[SYSTEM] Initiating Manual Clip Ingest Bypass...")
    result = execute_clip_ingest(instruction="Format this text into a clean, highly readable bulleted list. Fix grammar.")
    print(result)
