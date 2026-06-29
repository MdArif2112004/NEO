import sys
import json
import os
import random
import requests
from datetime import datetime
from pathlib import Path

# Setup paths relative to this script
DIR_PATH = Path(__file__).parent
DATA_FILE = DIR_PATH / "data.json"

# ================= THE SYSTEM (ADMIN PROTOCOL) =================

def load_data():
    if not DATA_FILE.exists():
        print("[SYSTEM ERROR] data.json not found.")
        sys.exit(1)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def check_level_up(data):
    current_level = data["player"]["level"]
    new_level = data["player"]["xp"] // 1000
    if new_level > current_level:
        data["player"]["level"] = new_level
        data["player"]["skill_points"] += (new_level - current_level)
        print(f"\n[SYSTEM ALERT] LEVEL UP! You are now Level {new_level}.")
        print(f"[SYSTEM ALERT] +{new_level - current_level} Skill Points awarded.")
    return data

def display_status():
    data = load_data()
    p = data["player"]
    s = data["skills"]
    
    # Red Gate Monday Protocol Roll
    today = datetime.now().strftime("%A")
    if today == "Monday" and data["tracking"]["last_login"] != datetime.now().strftime("%Y-%m-%d"):
        roll = random.randint(1, 100)
        if roll <= 10:
            p["world_state"] = "RED GATE"
            print("🚨 [ALERT: RED GATE OPENED. Difficulty Doubled for 72 Hours.] 🚨\n")
        else:
            p["world_state"] = "Normal"
            
    data["tracking"]["last_login"] = datetime.now().strftime("%Y-%m-%d")
    save_data(data)

    print("="*40)
    print("        S Y S T E M   C O N S O L E      ")
    print("="*40)
    print(f"🌍 World State : {p['world_state']}")
    print(f"👤 Rank / Level: Level {p['level']}")
    print(f"⚡ Current XP  : {p['xp']} / {((p['level']+1)*1000)}")
    print(f"💰 Gold Balance: {p['gold']}")
    print(f"💎 Skill Points: {p['skill_points']}")
    print("-" * 40)
    print("⚔️ SKILL CALIBRATION:")
    for skill, level in s.items():
        print(f"  > {skill.replace('_', ' ').title().ljust(16)} : Lv {level}")
    print("="*40)
    print("\n[PENDING QUEST]: The 10/30 Protocol (10m Mind + 30m Body).")

def log_workout():
    data = load_data()
    p = data["player"]
    
    multiplier = 2 if p["world_state"] == "RED GATE" else 1
    xp_gain = 75 * multiplier
    gold_gain = 35 * multiplier
    
    p["xp"] += xp_gain
    p["gold"] += gold_gain
    data["tracking"]["streak"] += 1
    
    print("\n[PROCESSING] 10/30 High-Density Protocol Validated.")
    print(f"[ACCEPTED] Intensity: MAX. Quest Complete (Rank D).")
    print(f"[REWARD] +{xp_gain} XP | +{gold_gain} Gold.")
    
    data = check_level_up(data)
    save_data(data)


# ================= THE SHADOW INSTRUCTOR (AI PROTOCOL) =================

def ask_instructor(query):
    # Try Groq first (fastest for instructor), fallback to generic error
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[SYSTEM WARNING] GROQ_API_KEY not found in environment. Instructor offline.")
        return

    system_prompt = """You are 'The Shadow Instructor,' a Grandmaster Sensei guiding the User to Monarch status.
Tone: Strict, Visionary, Wise, Lethal, Efficient. 
Constraint: User is in a single room. 
If asked for a drill, pull from the 10/30 Compressed protocol and micro-dose rules (e.g., shadow boxing, stealth walking)."""

    print("\n[Instructor is evaluating your request...]")
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                "temperature": 0.3
            },
            timeout=15
        )
        data = response.json()
        print("\n" + "="*50)
        print(f"🩸 THE SHADOW INSTRUCTOR:")
        print("="*50)
        print(data["choices"][0]["message"]["content"])
        print("="*50 + "\n")
    except Exception as e:
        print(f"[SYSTEM ERROR] Instructor transmission failed: {e}")

# ================= CLI ROUTER =================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python app.py [status | log | ask 'your question']")
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "status":
        display_status()
    elif command == "log":
        log_workout()
    elif command == "ask":
        if len(sys.argv) > 2:
            ask_instructor(" ".join(sys.argv[2:]))
        else:
            print("[SYSTEM ERROR] You must provide a query. (e.g., python app.py ask 'Give me today's combat drill')")
    else:
        print("[SYSTEM ERROR] Unknown command.")
