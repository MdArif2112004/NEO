"""
neo/tools/discord_spider.py
===========================
Authorized Discord Bounty Spider — Freelance Gig Scanner.
Monitors targeted servers/channels for high-value keyword matches
and routes hits through notification_server.py for desktop alerts.
RAM Constraint: 8GB (Event-driven, no memory pooling).
"""
import os
import json
import requests
import discord
from datetime import datetime

# ── Notification routing ──
NOTIFICATION_SERVER_URL = "http://127.0.0.1:51820/"
try:
    from win10toast import ToastNotifier
    FALLBACK_TOASTER = ToastNotifier()
    HAS_FALLBACK = True
except ImportError:
    FALLBACK_TOASTER = None
    HAS_FALLBACK = False

# ── The Hunt Matrix ──
TARGET_KEYWORDS = ["python", "scraping", "automation", "bot", "data pipeline", "AI agent"]

# Substring match (case-insensitive) against guild names
TARGET_SERVER_FRAGMENTS = ["freelance", "programmer"]

# Substring match against channel names (lowercased)
TARGET_CHANNEL_FRAGMENTS = ["hire", "gig", "freelance", "job", "work"]

LOG_FILE = "bounty_leads.txt"
FREELANCE_PIPELINE_ID_FILE = "freelance_pipeline_id.json"

# Notion auth (reuse pattern from notion_api.py)
NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# Authorized Bot Intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


def send_notification(title: str, message: str, duration: int = 6):
    """Route alert through notification_server.py; fallback to direct win10toast."""
    try:
        import urllib.request
        payload = json.dumps({
            "title": title,
            "message": message,
            "duration": duration
        }).encode()
        req = urllib.request.Request(
            NOTIFICATION_SERVER_URL,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=2)
        return True
    except Exception:
        if HAS_FALLBACK and FALLBACK_TOASTER is not None:
            try:
                FALLBACK_TOASTER.show_toast(title, message, duration=duration, threaded=True)
                return True
            except Exception:
                pass
    return False


def log_bounty(author, server, channel, content, link):
    """Writes the intercepted bounty to a local ledger."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] SERVER: {server} | CHANNEL: #{channel} | USER: {author}\n"
        f"CONTENT: {content}\n"
        f"LINK: {link}\n"
        f"{'-' * 60}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)


def _get_freelance_db_id():
    """Get the Freelance Pipeline Notion database ID from local file."""
    try:
        with open(FREELANCE_PIPELINE_ID_FILE, "r") as f:
            data = json.load(f)
            return data.get("database_id")
    except Exception:
        return None


def log_to_notion(server_name, channel_name, content, jump_link):
    """
    Fire-and-forget: Log the bounty hit to the Freelance Pipeline Notion database.
    Silent fail if Notion is down or the database doesn't exist.
    """
    try:
        db_id = _get_freelance_db_id()
        if not db_id:
            return  # Database not set up yet

        payload = {
            "parent": {"database_id": db_id},
            "properties": {
                "Platform": {"select": {"name": "Discord"}},
                "Gig Title": {"title": [{"type": "text", "text": {"content": content[:100]}}]},
                "Status": {"select": {"name": "New"}},
                "Link": {"url": jump_link},
                "Date Found": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
                "Notes": {"rich_text": [{"type": "text", "text": {"content": f"{server_name} | #{channel_name}"}}]},
            },
        }

        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=NOTION_HEADERS,
            json=payload,
            timeout=5,
        )
        if resp.status_code == 200:
            print(f"   📝 Logged to Notion Freelance Pipeline")
    except Exception:
        pass  # Silent fail — Notion logging is non-critical


@client.event
async def on_ready():
    print(f"🕷️ [SPIDER ONLINE] Authorized as {client.user}.")
    print(f"📡 Scanning servers containing: {', '.join(TARGET_SERVER_FRAGMENTS)}")
    print(f"📡 Channel filter: {', '.join(TARGET_CHANNEL_FRAGMENTS)}")
    print(f"🎯 Keywords: {', '.join(TARGET_KEYWORDS)}")
    print(f"🔔 Notifications via: {NOTIFICATION_SERVER_URL}")
    print(f"📝 Logging to: {LOG_FILE}")


def _guild_matches(guild_name: str) -> bool:
    """Check if guild name contains any of the target server fragments."""
    name_lower = guild_name.lower()
    return any(frag in name_lower for frag in TARGET_SERVER_FRAGMENTS)


def _channel_matches(channel_name: str) -> bool:
    """Check if channel name contains any target channel fragments."""
    name_lower = channel_name.lower()
    return any(frag in name_lower for frag in TARGET_CHANNEL_FRAGMENTS)


@client.event
async def on_message(message):
    # Ignore our own bot to prevent feedback loops
    if message.author == client.user:
        return

    # Server filter: only process whitelisted guilds
    if not message.guild:
        return  # Skip DMs
    if not _guild_matches(message.guild.name):
        return

    # Channel filter: only process matched channels
    channel_name = message.channel.name if hasattr(message.channel, "name") else ""
    if not _channel_matches(channel_name):
        return

    # Keyword match
    content_lower = message.content.lower()
    matched_keywords = [kw for kw in TARGET_KEYWORDS if kw in content_lower]
    if not matched_keywords:
        return

    jump_link = (
        f"https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
        if message.guild else "Direct Message"
    )
    server_name = message.guild.name
    author_name = str(message.author)
    preview = message.content[:280]

    print(f"\n🎯 [BOUNTY DETECTED] Server: {server_name} | #{channel_name} | User: {author_name}")
    print(f"   Keywords: {', '.join(matched_keywords)}")
    print(f"   Preview: {preview[:120]}...")

    # Log to local disk
    log_bounty(author_name, server_name, channel_name, preview, jump_link)

    # Desktop alert via notification_server (with fallback)
    alert_title = f"🎯 Gig: {', '.join(matched_keywords)}"
    alert_msg = f"Server: {server_name}\n#{channel_name}\nAuthor: {author_name}"
    send_notification(alert_title, alert_msg, duration=6)

    # Log to Notion Freelance Pipeline (fire-and-forget)
    log_to_notion(server_name, channel_name, preview, jump_link)


def execute_spider():
    """Entry point — called from start_neo.bat or standalone."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ [SYSTEM FAULT] DISCORD_BOT_TOKEN not found in environment variables.")
        return
    client.run(token)


if __name__ == "__main__":
    execute_spider()