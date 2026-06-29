"""
neo/tools/screen.py
===================
Screen capture and OCR.
Neo can read what's on screen — including ChatGPT responses.
"""

import os
import time
from pathlib import Path


def read_screen(region=None) -> str:
    """
    Capture current screen and return OCR text.
    region: (x, y, width, height) tuple or None for full screen.
    Requires: pip install pillow pytesseract pyautogui
    Also requires: tesseract-ocr installed on system
    """
    try:
        import pyautogui
        import pytesseract
        from PIL import Image

        screenshot = pyautogui.screenshot(region=region)
        text = pytesseract.image_to_string(screenshot, lang="eng")
        text = text.strip()

        if not text:
            return "Screen captured but no text found (maybe try a specific region)"
        return f"[Screen text]\n{text}"

    except ImportError as e:
        return (
            f"Missing dependency: {e}\n"
            "Run: pip install pillow pytesseract pyautogui\n"
            "And: sudo apt install tesseract-ocr  (Linux) or brew install tesseract (Mac)"
        )
    except Exception as e:
        return f"Screen read error: {e}"


def capture_chatgpt() -> str:
    """
    DEPRECATED — UI Scraping (Direct Endpoint Mandate violation).
    ===========
    This function scrapes the ChatGPT web UI via OCR, which is fragile
    and breaks whenever the frontend layout changes.

    PERMANENT FIX: Use the ChatGPT / Gemini API endpoint directly instead.
    ======================================================================
    Returning a deprecation warning to redirect to API-based alternatives.

    To capture LLM responses, use one of these instead:
      - neo/tools/web_researcher.py -> generate_research_report(topic)
      - neo/tools/filesystem.py -> ask_gemini_web(massive_prompt)
      - Direct API call via neo/llm/model.py -> get_model().chat(...)
    """
    return (
        "[DEPRECATED - UI Scraping Collapse Protection]\n"
        "capture_chatgpt() uses fragile screen OCR on the ChatGPT web UI, "
        "which is banned under the Direct Endpoint Mandate.\n"
        "Use one of these instead:\n"
        "  - ask_gemini_web(prompt) - Direct API call through the LLM failover\n"
        "  - generate_research_report(topic) - Structured web research\n"
        "  - get_model().chat(...) - Raw API access via neo/llm/model.py"
    )


def save_screenshot(path: str = None) -> str:
    """Save a screenshot to disk for debugging."""
    try:
        import pyautogui
        save_path = Path(path) if path else Path.home() / ".neo" / f"screen_{int(time.time())}.png"
        save_path.parent.mkdir(exist_ok=True)
        pyautogui.screenshot(str(save_path))
        return f"Screenshot saved: {save_path}"
    except Exception as e:
        return f"Screenshot error: {e}"
