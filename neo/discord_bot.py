"""
neo/discord_bot.py
==================
Two-Way Command & Control Bridge.
Listens for commands in Discord and routes them to the N.E.O. ReAct core.
Isolated from outbound webhook tools.
"""
import os
import sys
from pathlib import Path

# Mechanical Patch: Dynamically resolve project root and inject into sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import discord
import asyncio
from neo.brain import run as execute_neo_task

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"📡 [C&C Bot Active] Logged in as {client.user}")
    print("Awaiting directives starting with '!neo '...")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.lower().startswith("!neo "):
        directive = message.content[5:].strip()
        if not directive:
            return
            
        print(f"\n[Discord C&C] Intercepted Directive: {directive}")
        await message.channel.send("⚡ `[N.E.O. Processing Directive...]`")
        
        try:
            # Wrap synchronous brain execution to keep the async bot loop alive
            result = await asyncio.to_thread(execute_neo_task, directive)
            
            response = f"**[MISSION ACCOMPLISHED]**\n```\n{result}\n```"
            
            if len(response) > 1999:
                await message.channel.send(response[:1990] + "...\n```")
            else:
                await message.channel.send(response)
                
        except Exception as e:
            await message.channel.send(f"❌ `[SYSTEM FAULT]: {str(e)}`")

def start_bot():
    """Ignites the Discord listener."""
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ [Discord C&C] Missing DISCORD_BOT_TOKEN environment variable.")
        return
        
    client.run(token)

if __name__ == "__main__":
    start_bot()
