"""
neo/tools/system_audio.py
=========================
Plays custom UI sounds for Success and Alerts, and harsh system sounds for Errors.
"""
import winsound
import os

def play_audio_cue(cue_type: str = "success") -> str:
    """Plays an audio cue. cue_type can be 'success', 'alert', or 'error'."""
    try:
        if cue_type == "success":
            if os.path.exists("success.wav"):
                # Plays your custom power-up sound
                winsound.PlaySound("success.wav", winsound.SND_FILENAME)
            else:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
                
        elif cue_type == "alert":
            if os.path.exists("alert.wav"):
                # Plays your custom attention sound
                winsound.PlaySound("alert.wav", winsound.SND_FILENAME)
            else:
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
                
        elif cue_type == "error":
            # Keeps the harsh Windows default sound for actual crashes
            winsound.MessageBeep(winsound.MB_ICONHAND)
            
        else:
            winsound.MessageBeep(winsound.MB_OK)
            
        return f"✅ Played '{cue_type}' audio cue."
    except Exception as e:
        return f"❌ Audio failed: {e}"
