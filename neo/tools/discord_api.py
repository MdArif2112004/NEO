"""
neo/tools/discord_api.py
========================
Asynchronous telemetry link to the Discord Command Hub.
"""
import os
import requests

def ping_discord(channel: str, message: str, payload: str = "") -> str:
    """
    Pings the Discord Command Hub via Webhooks.
    channel options: 'factory', 'operator', 'converter', 'system'
    """
    webhooks = {
        "factory": os.environ.get("DISCORD_WH_FACTORY"),
        "operator": os.environ.get("DISCORD_WH_OPERATOR"),
        "converter": os.environ.get("DISCORD_WH_CONVERTER"),
        "system": os.environ.get("DISCORD_WH_SYSTEM")
    }
    
    url = webhooks.get(channel.lower())
    if not url:
        return f"❌ DISCORD FAULT: Webhook for '{channel}' not found in Environment Variables."

    data = {"content": message}
    
    # String concatenation bypasses formatting crashes
    if payload:
        data["content"] += "\n\n```text\n" + str(payload)[:1500] + "\n```"

    try:
        response = requests.post(url, json=data, timeout=5)
        if response.status_code in [200, 204]:
            return f"✅ TRANSMISSION SUCCESS: Logged to [{channel.upper()}]."
        else:
            return f"❌ DISCORD REJECTED PAYLOAD. Status: {response.status_code}"
    except Exception as e:
        return f"❌ DISCORD CONNECTION FAULT: {str(e)}"
