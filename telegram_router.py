"""
telegram_router.py
==================
Listens to Telegram messages and routes them directly to Neo's Brain.
"""
import os
import time
import requests
from neo.brain import NeoBrain

# Read token from environment
BOT_TOKEN = os.environ.get("NEO_TELEGRAM_TOKEN", "")

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

def main():
    print("📡 Telegram Router Online. Waiting for messages...")
    neo = NeoBrain()
    offset = None
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            params = {"timeout": 100, "offset": offset}
            response = requests.get(url, params=params).json()
            
            for result in response.get("result", []):
                offset = result["update_id"] + 1
                message = result.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")
                
                if text and chat_id:
                    print(f"\n[Telegram] Received command: {text}")
                    send_message(chat_id, f"⚙️ Neo is processing: '{text}'...")
                    
                    # Route to Neo
                    summary = neo.run(text)
                    
                    # Send result back to your phone
                    send_message(chat_id, f"✅ Neo Finished:\n{summary}")
                    
        except Exception as e:
            time.sleep(5) # Sleep on connection error to prevent spamming

if __name__ == "__main__":
    main()
