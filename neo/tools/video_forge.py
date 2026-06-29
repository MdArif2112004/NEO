"""
neo/tools/video_forge.py
========================
Phase 4: Visual Assembly Line.
Takes the generated audio files and overlays them onto a looping background video,
formatting the output to 9:16 (YouTube Shorts/TikTok) specifications.
Optimized for 8GB RAM local machines.
"""
import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

def render_shorts(audio_dir="audio", bg_video="gameplay.mp4", output_dir="renders") -> str:
    """Assembles audio and background video into a 9:16 short."""
    if not os.path.exists(audio_dir):
        return f"❌ FORGE FAULT: '{audio_dir}' directory not found."
    if not os.path.exists(bg_video):
        return f"❌ FORGE FAULT: Background video '{bg_video}' not found in root directory."
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
    if not audio_files:
        return "❌ FORGE FAULT: No .mp3 files found to render."

    success_count = 0
    print("\n[FORGE] Initiating Headless Video Rendering...")

    try:
        # Load the background video (we only load it once to save RAM)
        base_bg = VideoFileClip(bg_video)
        
        for audio_file in audio_files:
            audio_path = os.path.join(audio_dir, audio_file)
            output_filename = audio_file.replace('.mp3', '.mp4')
            output_path = os.path.join(output_dir, output_filename)
            
            # Skip if already rendered
            if os.path.exists(output_path):
                continue
                
            print(f"  -> Assembling: {output_filename}...")
            
            audio_clip = AudioFileClip(audio_path)
            audio_duration = audio_clip.duration
            
            # If the audio is longer than the background video, we fail out for safety.
            if audio_duration > base_bg.duration:
                print(f"  ❌ Skipping {output_filename}: Audio ({audio_duration}s) is longer than BG video ({base_bg.duration}s).")
                audio_clip.close()
                continue
                
            # Pick a random starting point in the gameplay video so every short looks unique
            max_start = base_bg.duration - audio_duration
            start_time = random.uniform(0, max_start)
            
            # Cut the background video to match the audio length perfectly
            bg_clip = base_bg.subclip(start_time, start_time + audio_duration)
            
            # Crop to 9:16 Vertical format (1080x1920 ratio)
            # We crop the center of the video
            w, h = bg_clip.size
            target_ratio = 9 / 16
            target_width = int(h * target_ratio)
            x_center = w / 2
            
            bg_clip = bg_clip.crop(
                x1=x_center - target_width/2, 
                y1=0, 
                x2=x_center + target_width/2, 
                y2=h
            )
            
            # Resize standard to 720x1280 to save render time and RAM
            bg_clip = bg_clip.resize(height=1280, width=720)
            
            # Attach the generated AI voice to the video
            final_video = bg_clip.set_audio(audio_clip)
            
            # Render the final file. 
            # We use fast presets and low threads to prevent CPU thermal throttling.
            final_video.write_videofile(
                output_path, 
                codec="libx264", 
                audio_codec="aac", 
                fps=30, 
                preset="ultrafast", 
                threads=2,
                logger=None # Supress messy output
            )
            
            # Free RAM
            audio_clip.close()
            final_video.close()
            success_count += 1
            
        base_bg.close()
        
    except Exception as e:
        return f"❌ FORGE FAULT: Rendering crash: {str(e)}"

    if success_count == 0:
        return "✅ FORGE COMPLETE: All videos already rendered."

    return f"✅ FORGE COMPLETE: {success_count} YouTube Shorts successfully rendered to '{output_dir}/'."

if __name__ == "__main__":
    import sys
    import io
    # Force Windows terminal to accept UTF-8 Emojis
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    print(render_shorts())
