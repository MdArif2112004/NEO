"""
neo/tools/system_audio.py
=========================
Plays custom UI sounds for Success and Alerts, and harsh system sounds for Errors.
Cross-platform: winsound on Windows, paplay/aplay on Linux, afplay on macOS.
"""
import os
import shutil
import subprocess
import sys

IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

if IS_WINDOWS:  # Windows-only stdlib module
    import winsound  # type: ignore


def _play_file(path: str) -> bool:
    """Play a .wav with the platform's native player. False if unavailable."""
    if not os.path.exists(path):
        return False
    try:
        if IS_WINDOWS:
            winsound.PlaySound(path, winsound.SND_FILENAME)  # type: ignore[name-defined]
        elif IS_MAC:
            subprocess.Popen(["afplay", path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            player = shutil.which("paplay") or shutil.which("aplay")
            if not player:
                return False
            subprocess.Popen([player, path],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _system_beep(kind: str = "ok") -> None:
    """Fallback beep when no custom .wav is present."""
    try:
        if IS_WINDOWS:
            codes = {
                "ok": winsound.MB_OK,  # type: ignore[name-defined]
                "info": winsound.MB_ICONASTERISK,  # type: ignore[name-defined]
                "warn": winsound.MB_ICONEXCLAMATION,  # type: ignore[name-defined]
                "err": winsound.MB_ICONHAND,  # type: ignore[name-defined]
            }
            winsound.MessageBeep(codes.get(kind, codes["ok"]))  # type: ignore[name-defined]
        else:
            # Terminal BEL — dependency-free on Linux/macOS
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        pass


def play_audio_cue(cue_type: str = "success") -> str:
    """Plays an audio cue. cue_type can be 'success', 'alert', or 'error'."""
    try:
        if cue_type == "success":
            if not _play_file("success.wav"):
                _system_beep("info")
        elif cue_type == "alert":
            if not _play_file("alert.wav"):
                _system_beep("warn")
        elif cue_type == "error":
            _system_beep("err")
        else:
            _system_beep("ok")
        return f"✅ Played '{cue_type}' audio cue."
    except Exception as e:
        return f"❌ Audio failed: {e}"
