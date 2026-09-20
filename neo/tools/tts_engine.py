"""
neo/tools/tts_engine.py
=======================
Phase 3: Acoustic Synthesis.
Reads text files from the scripts directory and generates studio-quality 
neural voiceovers using free Microsoft Edge TTS endpoints.
"""
import os
import asyncio
import edge_tts

# We use a deep, authoritative American male voice suitable for Tech/Finance Shorts
VOICE = "en-US-ChristopherNeural"

async def generate_audio(text: str, output_path: str):
    """Asynchronously generates audio from text using edge-tts."""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(output_path)

def generate_voiceovers(script_dir="scripts", audio_dir="audio") -> str:
    """Reads all .txt scripts and converts them to .mp3 voiceovers."""
    if not os.path.exists(script_dir):
        return f"❌ AUDIO FAULT: Directory '{script_dir}' does not exist. Run scriptwriter first."

    if not os.path.exists(audio_dir):
        os.makedirs(audio_dir)

    scripts = [f for f in os.listdir(script_dir) if f.endswith('.txt')]
    if not scripts:
        return f"❌ AUDIO FAULT: No text files found in '{script_dir}'."

    success_count = 0
    print("\n[AUDIO] Initiating Neural Synthesis...")

    for script_file in scripts:
        script_path = os.path.join(script_dir, script_file)
        audio_filename = script_file.replace('.txt', '.mp3')
        audio_path = os.path.join(audio_dir, audio_filename)
        
        # Skip if we already generated audio for this script
        if os.path.exists(audio_path):
            continue

        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_text = f.read().strip()
                
            if not script_text:
                continue
                
            print(f"  -> Synthesizing: {audio_filename}...")
            
            # edge-tts requires asyncio to run
            asyncio.run(generate_audio(script_text, audio_path))
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Failed to synthesize {script_file}: {str(e)}")

    if success_count == 0:
        return "✅ AUDIO COMPLETE: All scripts already have corresponding audio files."

    return f"✅ AUDIO SYNTHESIS COMPLETE: {success_count} voiceovers generated in '{audio_dir}/'."
