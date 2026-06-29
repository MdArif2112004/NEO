"""
neo/tools/neo_voice.py
======================
Advanced Audio Subsystem for Continuous Acoustic Ingestion & Output
"""
import speech_recognition as sr

def speak(text: str) -> str:
    """
    Vocal Output Protocol. 
    Speaks the given text out loud using local system TTS.
    """
    import os
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
        return f"✅ Spoken: {text}"
    except ImportError:
        # Zero-dependency Windows fallback using PowerShell
        clean_text = text.replace("'", "").replace('"', "")
        os.system(f'powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{clean_text}\')"')
        return f"✅ Spoken (Fallback): {text}"
    except Exception as e:
        return f"❌ Vocal Protocol Fault: {str(e)}"

def capture_operator_directive() -> str:
    """
    Maintains an open continuous listening track for 40 seconds.
    Forced hardware indexing to bypass Windows phantom mapping.
    """
    recognizer = sr.Recognizer()
    
    # --- Advanced Audio Engineering Calibration Matrix ---
    recognizer.energy_threshold = 300 
    recognizer.dynamic_energy_threshold = False
    
    # --- The Hearing Fix Parameters ---
    recognizer.pause_threshold = 2.0    # Allows 2-second pause to think
    recognizer.phrase_threshold = 0.3   
    recognizer.non_speaking_duration = 1.2 

    # Hardware override: device_index=1
    with sr.Microphone(device_index=1) as source:
        try:
            print("[Neo Voice] 🟢 Listening... Directives are live.")
            
            # Open Ingestion Window
            audio_stream = recognizer.listen(source, timeout=10, phrase_time_limit=40)
            
            print("[Neo Voice] 🧠 Processing voice stream...")
            
            transcription = recognizer.recognize_google(audio_stream)
            print(f"[Neo Voice] 📬 Audio resolved: \"{transcription}\"")
            return transcription

        except sr.WaitTimeoutError:
            print("[Neo Voice] ⚠️ Idle Timeout: No starting input detected.")
            return "ERROR_TIMEOUT"
        except sr.UnknownValueError:
            print("[Neo Voice] ❌ Unresolved Data: Sound detected but could not extract linguistic words.")
            return "ERROR_UNRESOLVED"
        except Exception as e:
            print(f"[Neo Voice] ❌ Physical Subsystem Fault: {e}")
            return f"ERROR_FAULT: {e}"

if __name__ == "__main__":
    # Isolated test run to check system limits directly
    speak("Voice matrix initialized.")
    result = capture_operator_directive()
    print(f"Final Transcript Output: {result}")
