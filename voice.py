"""
voice.py — NEO Voice (Vosk offline STT + command grammar + pyttsx3 TTS)
Grammar-locked: NEO can only hear the phrases in ACTIONS, so "open youtube"
cannot be misheard as "open you to". Offline, 8GB-safe.
Deps: pip install vosk sounddevice pyttsx3
"""
import os, sys, json, queue, time, subprocess, webbrowser
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from neo.tools.neo_voice import speak
import urllib.parse
from groq import Groq

DIR        = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(DIR, "state.txt")
MODEL_PATH = os.path.join(DIR, "models", "vosk-en")
SAMPLE_RATE = 16000
MIC_DEVICE  = None   # None = default mic. Set to your index from Step 0 if default is wrong.
_model      = None   # loaded by main(), reused by listen_free()

def _set_state(s):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(s)
    except Exception:
        pass

def listen_free(seconds=6):
    """Free-vocabulary Vosk capture (no grammar). Reuses the loaded model."""
    import queue as _queue
    rec = KaldiRecognizer(_model, SAMPLE_RATE)  # no grammar => free vocab
    q = _queue.Queue()
    def cb(indata, frames, t, status):
        q.put(bytes(indata))
    text_parts = []
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
                           channels=1, device=MIC_DEVICE, callback=cb):
        deadline = time.time() + seconds
        while time.time() < deadline:
            data = q.get()
            if rec.AcceptWaveform(data):
                partial = json.loads(rec.Result()).get("text", "").strip()
                if partial:
                    text_parts.append(partial)
    final = json.loads(rec.FinalResult()).get("text", "").strip()
    if final:
        text_parts.append(final)
    return " ".join(text_parts)

def _ask_neo():
    speak("Listening.")
    text = listen_free(seconds=6)
    if not text:
        return
    try:
        client = Groq()
        reply = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are NEO, a terminal assistant. Answer in ONE short spoken sentence. No markdown, no lists."},
                {"role": "user", "content": text},
            ],
        ).choices[0].message.content
        if reply:
            reply = reply.strip()
        speak(reply or "")
    except Exception:
        speak("Groq is unreachable.")

def _search_youtube():
    speak("Say your search.")
    text = listen_free(seconds=6)
    if not text:
        return
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(text))
    speak("Opening results.")

ACTIONS = {
    "open youtube":    lambda: webbrowser.open("https://youtube.com"),
    "open notion":     lambda: webbrowser.open("https://notion.so"),
    "open chrome":     lambda: webbrowser.open("https://google.com"),
    "sweep jobs":      lambda: [webbrowser.open(u) for u in (
                            "https://himalayas.app/jobs?q=data+cleaning&sort=recent",
                            "https://himalayas.app/jobs?q=notion+operations&sort=recent")],
    "vision strike":   lambda: subprocess.Popen([sys.executable, "neo/tools/vision_strike.py"]),
    "what time is it": lambda: speak(time.strftime("It is %I:%M %p")),
    "ask neo":         _ask_neo,
    "search youtube":  _search_youtube,
}
COMMANDS = list(ACTIONS.keys())
GRAMMAR  = json.dumps(COMMANDS + ["[unk]"])

def main():
    if not os.path.isdir(MODEL_PATH):
        print(f"[VOICE] Vosk model missing at {MODEL_PATH}")
        return
    global _model
    model = Model(MODEL_PATH)
    _model = model
    rec = KaldiRecognizer(model, SAMPLE_RATE, GRAMMAR)
    q = queue.Queue()

    def cb(indata, frames, t, status):
        q.put(bytes(indata))

    _set_state("idle")
    print(f"[VOICE] Online. Commands: {COMMANDS}")
    try:
        speak("Neo online.")
    except Exception:
        pass

    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000, dtype="int16",
                           channels=1, device=MIC_DEVICE, callback=cb):
        _set_state("listening")
        while True:
            data = q.get()
            if not rec.AcceptWaveform(data):
                continue
            cmd = json.loads(rec.Result()).get("text", "").strip()
            if cmd not in ACTIONS:
                continue
            print(f"[VOICE] -> {cmd}")
            _set_state("processing")
            try:
                ACTIONS[cmd]()
            except Exception as e:
                print(f"[VOICE] action fault: {e}")
            _set_state("listening")

if __name__ == "__main__":
    main()