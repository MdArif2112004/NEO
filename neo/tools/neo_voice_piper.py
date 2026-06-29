"""
neo_voice_piper.py — Piper offline TTS for NEO (replaces ElevenLabs).
Deps: pip install piper-tts ; a voice .onnx + .onnx.json in models/piper/
"""
import os, sys, subprocess, tempfile, winsound

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VOICE = os.path.join(BASE, "models", "piper", "en_GB-alan-medium.onnx")

def speak(text: str):
    out = os.path.join(tempfile.gettempdir(), "neo_say.wav")
    try:
        subprocess.run([sys.executable, "-m", "piper", "--model", VOICE,
                        "--output_file", out],
                       input=text.encode("utf-8"), check=True)
        winsound.PlaySound(out, winsound.SND_FILENAME)
    except Exception as e:
        print(f"[NEO VOICE] {e}")

if __name__ == "__main__":
    speak("Neo online. Voice systems nominal.")