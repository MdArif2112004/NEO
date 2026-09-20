"""
neo/tools/arbitrage.py
======================
The "Invisible Arbitrage" Content Engine.
Automates high-retention video asset generation (TTS + Prompt Extraction) at zero cost.
"""
import os
import asyncio
import edge_tts
from neo.tools.discord_api import ping_discord

# Tactical Voice Profile: Deep, authoritative male
VOICE_MODEL = "en-US-ChristopherNeural" 

async def generate_tts(text: str, output_path: str):
    """Hits the Azure Neural TTS endpoints for free."""
    communicate = edge_tts.Communicate(text, VOICE_MODEL)
    await communicate.save(output_path)

def execute_arbitrage_pipeline(project_name: str, script_json: list) -> str:
    """
    Takes a structured JSON script, creates the media folders, 
    generates the AI voiceovers, and extracts the visual prompts.
    """
    # 1. Establish the Local Kill Box (Folder Structure)
    base_dir = os.path.abspath(os.path.join(os.getcwd(), "media", "channel_1", project_name))
    audio_dir = os.path.join(base_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    prompt_file = os.path.join(base_dir, "master_prompts.txt")
    
    print(f"\n[ARBITRAGE ENGINE] Initializing Project: {project_name}")
    print(f"[ARBITRAGE ENGINE] Target Directory: {base_dir}")

    formatted_prompts = "🎬 MASTER VISUAL PROMPTS (Copy/Paste to Leonardo.ai / Bing)\n"
    formatted_prompts += "="*60 + "\n\n"

    try:
        # 2. Iterate through the script blocks
        for index, block in enumerate(script_json):
            scene_num = str(index + 1).zfill(2)
            audio_text = block.get("audio", "")
            visual_prompt = block.get("visual", "")
            
            # Generate Audio
            if audio_text:
                audio_filename = os.path.join(audio_dir, f"scene_{scene_num}.mp3")
                print(f"  -> Rendering Audio {scene_num}...")
                asyncio.run(generate_tts(audio_text, audio_filename))
            
            # Format Prompts for the Operator
            if visual_prompt:
                formatted_prompts += f"--- SCENE {scene_num} ---\n"
                formatted_prompts += f"PROMPT: {visual_prompt}\n"
                formatted_prompts += f"NEGATIVE: 3d, photorealistic, ugly, distorted, text, watermark\n\n"

        # 3. Save the Prompts File
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(formatted_prompts)

        # 4. Ping the Command Hub
        discord_msg = (
            f"**ARBITRAGE DEPLOYMENT COMPLETE**\n"
            f"**Project:** `{project_name}`\n"
            f"**Assets Rendered:** `{len(script_json)} audio files`\n"
            f"**Location:** `{base_dir}`\n"
            f"Awaiting Operator visual generation."
        )
        ping_discord("system", discord_msg)

        return f"✅ Arbitrage Pipeline Complete. Assets saved to {base_dir}"

    except Exception as e:
        error_msg = f"❌ Arbitrage Engine Fault: {str(e)}"
        ping_discord("system", error_msg)
        return error_msg
