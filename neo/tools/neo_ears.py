"""
neo_ears.py — Vosk offline STT for NEO. Listens to mic, returns text.
Updates state.txt so the notch dot shows listening/processing.
Deps: pip install vosk sounddevice
"""
import os, json, queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE, "models", "vosk-en")
STATE_FILE = os.path.join(BASE, "state.txt")
SAMPLE_RATE = 16000
_model = None

def _set_state(s):
    try:
        with open(STATE_FILE, "w") as f:
            f.write(s)
    except Exception:
        pass

def _get_model():
    global _model
    if _model is None:
        if not os.path.isdir(MODEL_PATH):
            raise FileNotFoundError(f"Vosk model missing at {MODEL_PATH}")
        _model = Model(MODEL_PATH)
    return _model

def listen_once():
    """Block until a phrase is spoken; return recognized text."""
    model = _get_model()
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    q = queue.Queue()
    def cb(indata, frames, t, status):
        q.put(bytes(indata))
    _set_state("listening")
    text = ""
    with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=8000,
                           dtype="int16", channels=1, callback=cb):
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result()).get("text", "")
                if text.strip():
                    break
    _set_state("processing")
    return text.strip()

if __name__ == "__main__":
    print("[NEO EARS] Speak now (Ctrl+C to stop)...")
    try:
        while True:
            print("  heard:", listen_once())
            _set_state("idle")
    except KeyboardInterrupt:
        _set_state("idle")
        print("\nstopped.")