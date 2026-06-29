"""
observer.py
===========
The "World-Class Mentor" Protocol. 
Pulses every 5 minutes, extracts 7-W context, logs memory, and offers elite suggestions.
"""
import time
import os
import json
from datetime import datetime
import google.generativeai as genai
from PIL import ImageGrab
import tkinter as tk
import re

# Set your Gemini Key
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_KEY)

DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(DIR, "observer_memory.json")

def show_mentor_suggestion(message):
    """Pops up a sleek, temporary notification on your screen."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.geometry(f"400x120+{root.winfo_screenwidth() - 420}+50") # Top right
    root.configure(bg="#0f0f13")
    
    lbl = tk.Label(root, text=f"🧠 Mentor Insight:\n{message}", 
                   fg="#00E5FF", bg="#0f0f13", font=("Segoe UI", 10, "bold"), 
                   justify="left", wraplength=380)
    lbl.pack(expand=True, fill="both", padx=10, pady=10)
    
    root.after(12000, root.destroy) # Stays for 12 seconds so you can read it
    root.mainloop()

def log_to_memory(data):
    """Saves the 7-W context to a running memory file so Neo learns your routines."""
    memory = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory = json.load(f)
        except:
            pass
    
    # Keep the last 1000 observations so the file doesn't get too large
    memory.append(data)
    if len(memory) > 1000:
        memory = memory[-1000:]
        
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)

def analyze_screen():
    print(f"\n[Observer] Taking pulse snapshot at {datetime.now().strftime('%H:%M:%S')}...")
    screenshot_path = "temp_pulse.png"
    ImageGrab.grab().save(screenshot_path)
    
    try:
        from groq import Groq
        import base64
        from io import BytesIO
        from PIL import Image

        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            print("[Observer] ❌ GROQ_API_KEY missing. Cannot execute mentor protocol.")
            return

        client = Groq(api_key=groq_key)

        # 1. Compress image for Groq 4MB limit
        img = Image.open(screenshot_path)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        prompt = """
        You are a World-Renowned Polymath, Tech Expert, and Life Mentor observing your protégé's computer screen.
        Analyze this screen deeply. I need you to output your response strictly as a JSON object.
        
        Extract the following:
        1. Context (7Ws): Who, What, When, Where, Why, Which, How is the user doing?
        2. Inferred Mood/State: Are they focused, scattered, gaming, researching, struggling?
        3. Elite Suggestion: If you have a HIGH-VALUE, specific piece of advice (e.g., "Use FancyZones for window snapping", "Close these 5 tabs to save RAM", "Switch to Claude for this specific task", "Take a 5 min break to stretch", "Use this hotkey instead"), provide it. 
        If everything is perfectly optimized, leave the suggestion empty ("").
        
        Output EXACTLY in this JSON format:
        {
          "activity_summary": "User is currently...",
          "inferred_state": "Focused / Scattered / etc",
          "7w_breakdown": {"what": "...", "where": "...", "why": "..."},
          "mentor_suggestion": "Your elite advice here, or empty string if none."
        }
        """
        
        # 2. Fire to Groq Llama 4
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
            temperature=0.1,
            max_tokens=1024
        )
        
        text = response.choices[0].message.content.strip()
        
        # Clean up Markdown JSON formatting if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()
            
        try:
            analysis = json.loads(text)
            analysis["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_to_memory(analysis)
            print("[Observer] Logged 7-W Context to Memory.")
            
            suggestion = analysis.get("mentor_suggestion", "")
            if suggestion and len(suggestion) > 5:
                print(f"[Mentor Suggestion] {suggestion}")
                show_mentor_suggestion(suggestion)
            else:
                print("[Observer] Workflow optimized. No interruption needed.")
                
        except json.JSONDecodeError:
            print("[Observer] Failed to parse JSON from AI.")
            
    except Exception as e:
        print(f"[Observer] Error: {e}")
    finally:
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

def main():
    print("👁️ World-Class Mentor Protocol Online. Analyzing every 5 minutes...")
    while True:
        analyze_screen()
        time.sleep(900) # 15 minutes

if __name__ == "__main__":
    main()
