"""
neo/tools/media_forge.py
========================
Automated Video Assembly Matrix (Channel 1 Factory).
Ingests script.txt and /assets/ directory. Outputs final_render.mp4.
RAM Constraint: 8GB Optimized (2-thread capping, method="compose").
"""
import os
import glob
import asyncio
import edge_tts
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

# Configuration Matrix
SCRIPT_FILE = "script.txt"
AUDIO_FILE = "voiceover.mp3"
ASSETS_DIR = "assets"
OUTPUT_FILE = "final_render.mp4"
RESOLUTION = (1080, 1920)  # Shorts / TikTok vertical format
VOICE_MODEL = "en-US-ChristopherNeural"  # Dramatic, deep male voice

def verify_infrastructure():
    """Ensures directories and files exist before execution."""
    if not os.path.exists(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)
        print(f"⚠️ [SYSTEM HALT] '{ASSETS_DIR}' folder missing. Created. Please populate with .jpg/.png files.")
        return False
    if not os.path.exists(SCRIPT_FILE):
        print(f"❌ [SYSTEM FAULT] '{SCRIPT_FILE}' missing. Drop your text payload here.")
        return False
    
    valid_images = [f for f in os.listdir(ASSETS_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not valid_images:
        print(f"❌ [SYSTEM FAULT] No visual assets found in '{ASSETS_DIR}'. Populate before rendering.")
        return False
        
    return True

async def generate_audio():
    print("🎙️ [TTS ENGINE] Igniting edge-tts generation...")
    with open(SCRIPT_FILE, "r", encoding="utf-8") as f:
        script_text = f.read().strip()
        
    if not script_text:
        raise ValueError("Script file is empty.")
        
    communicate = edge_tts.Communicate(script_text, VOICE_MODEL)
    await communicate.save(AUDIO_FILE)
    print("✅ [TTS COMPLETE] Audio payload secured.")

def assemble_matrix():
    print("🎬 [ASSEMBLY MATRIX] Calculating durations and rendering frames...")
    
    # Load audio to calculate sequence timing
    audio_clip = AudioFileClip(AUDIO_FILE)
    total_duration = audio_clip.duration
    
    # Retrieve and sort assets
    image_paths = sorted(glob.glob(os.path.join(ASSETS_DIR, "*.[pj][pn][g]")))
    total_images = len(image_paths)
    time_per_image = total_duration / total_images
    
    print(f"📊 [METRICS] Audio: {total_duration:.2f}s | Images: {total_images} | Duration per image: {time_per_image:.2f}s")
    
    # Construct video clips iteratively to manage RAM
    clips = []
    for img_path in image_paths:
        clip = (ImageClip(img_path)
                .with_duration(time_per_image)
                .resized(new_size=RESOLUTION) # Forces uniformity, preventing composition crashes
                .with_position("center"))
        clips.append(clip)
        
    # Compose the final matrix
    # method="compose" is mathematically slower but drastically reduces memory overflow
    final_video = concatenate_videoclips(clips, method="compose")
    final_video = final_video.with_audio(audio_clip)
    
    print("⚙️ [ENCODING] Initiating ffmpeg write sequence...")
    # Capped at 2 threads and 24fps to respect the 8GB local memory limit
    final_video.write_videofile(
        OUTPUT_FILE, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac", 
        threads=2,
        preset="fast"
    )
    
    # Memory flush
    final_video.close()
    audio_clip.close()
    print(f"✅ [MISSION COMPLETE] Render finalized: {OUTPUT_FILE}")

def execute_pipeline():
    if not verify_infrastructure():
        return
        
    try:
        # Run async TTS generation
        asyncio.run(generate_audio())
        # Run synchronous video assembly
        assemble_matrix()
    except Exception as e:
        print(f"❌ [CRITICAL FAULT] Pipeline collapse: {str(e)}")

if __name__ == "__main__":
    execute_pipeline()
