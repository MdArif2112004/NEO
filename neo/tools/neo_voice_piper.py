"""
neo_voice_piper.py — Piper offline TTS for NEO (replaces ElevenLabs).
Deps: pip install piper-tts ; a voice .onnx + .onnx.json in models/piper/
Playback is cross-platform: winsound (Windows), paplay/aplay (Linux), afplay (macOS).
"""
import os, sys, subprocess, tempfile, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VOICE = os.path.join(BASE, "models", "piper", "en_GB-alan-medium.onnx")


def _play(path: str) -> bool:
    """Play a wav file with the platform's native player."""
    try:
        if sys.platform.startswith("win"):
            import winsound  # Windows-only stdlib module
            winsound.PlaySound(path, winsound.SND_FILENAME)
        elif sys.platform == "darwin":
            subprocess.run(["afplay", path], check=False)
        else:
            player = shutil.which("paplay") or shutil.which("aplay")
            if not player:
                return False
            subprocess.run([player, path], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"[NEO VOICE] playback failed: {e}")
        return False

def speak(text: str):
    out = os.path.join(tempfile.gettempdir(), "neo_say.wav")
    try:
        subprocess.run([sys.executable, "-m", "piper", "--model", VOICE,
                        "--output_file", out],
                       input=text.encode("utf-8"), check=True)
        _play(out)
    except Exception as e:
        print(f"[NEO VOICE] {e}")

if __name__ == "__main__":
    speak("Neo online. Voice systems nominal.")