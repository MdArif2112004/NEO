import asyncio
import edge_tts
import os
import time

# The top Neural AI Voices available for free
VOICES = {
    "1. Jarvis (British Male 1)": "en-GB-RyanNeural",
    "2. Alfred (British Male 2)": "en-GB-ThomasNeural",
    "3. Friday (British Female 1)": "en-GB-SoniaNeural",
    "4. Cortana (American Female)": "en-US-AriaNeural"
}

TEXT = "Hello, Sir. I am Neo. My upgraded neural speech matrix is now online and fully operational."

async def preview_voices():
    print("🎙️ Downloading Voice Previews (This takes a few seconds)...\n")
    
    for name, voice_id in VOICES.items():
        print(f"▶️ Playing: {name}")
        filename = f"preview_{voice_id}.mp3"
        
        # Generates the high-quality MP3
        communicate = edge_tts.Communicate(TEXT, voice_id)
        await communicate.save(filename)
        
        # Plays the MP3 using Windows default player
        os.system(f"start {filename}") 
        time.sleep(5) # Pauses so the voices don't talk over each other
        
    print("\n✅ All previews generated. Check your media player!")

if __name__ == "__main__":
    asyncio.run(preview_voices())
