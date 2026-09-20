# NEO — Documentary Short Forge (MoviePy 2.x · captions OFF · 8GB-safe)
import os
from moviepy import VideoFileClip, AudioFileClip

def forge(video_path, audio_path, out="roman_pilot.mp4"):
    if not (os.path.exists(video_path) and os.path.exists(audio_path)):
        print("[-] Missing asset. Abort."); return

    audio = AudioFileClip(audio_path)
    video = VideoFileClip(video_path)

    dur = min(audio.duration, video.duration)
    if video.duration < audio.duration:
        print(f"[!] Clip ({video.duration:.1f}s) shorter than audio "
              f"({audio.duration:.1f}s) — voiceover will cut. Use a longer clip.")

    audio = audio.subclipped(0, dur)
    video = video.subclipped(0, dur)

    # center-crop to 9:16, then force 1080x1920
    w, h = video.size
    cw = h * 9 / 16
    x1 = (w - cw) / 2
    clip = (video.cropped(x1=x1, y1=0, x2=x1 + cw, y2=h)
                 .resized(new_size=(1080, 1920))
                 .with_audio(audio))

    # threads=1 + ultrafast = hard RAM cap for 8GB
    clip.write_videofile(out, fps=24, threads=1, preset="ultrafast",
                         codec="libx264", audio_codec="aac", logger="bar")

    for c in (audio, video, clip): c.close()
    print(f"[+] Output: {out}")

if __name__ == "__main__":
    forge("rome_stock.mp4", "rome_tts.mp3")