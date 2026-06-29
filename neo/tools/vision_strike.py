"""
neo/tools/vision_strike.py
==========================
[VISION STRIKE] - Screen Capture Optical Extraction Node.
RAM Constraint: 8GB Optimized (0MB local OCR processing, offloaded to cloud).
Authentication: OS-level Environment Variable.
"""
import os
import io
import base64
import requests
import pyperclip
from PIL import ImageGrab

# Hunt for the key in the OS environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
RAW_IMAGE_PATH = "screenshot.png"

def execute_vision_strike():
    print("📸 [VISION STRIKE] Triggering primary monitor capture...")
    
    if not GEMINI_API_KEY:
        print("❌ [SYSTEM FAULT] GEMINI_API_KEY missing from OS environment variables.")
        print("💡 Ensure you have set it via: setx GEMINI_API_KEY \"your_key\" (requires terminal restart)")
        return

    try:
        # Grab complete screen canvas
        screenshot = ImageGrab.grab()
        screenshot.save(RAW_IMAGE_PATH, "PNG")
        
        # Read and convert to base64 for pure HTTP payload carriage
        with open(RAW_IMAGE_PATH, "rb") as image_file:
            img_base64 = base64.b64encode(image_file.read()).decode("utf-8")
            
        print("📡 [CLOUD NODE] Processing canvas payload via Flash Engine...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [
                    {"text": "Extract every single piece of readable text, code, or data fields from this image exactly as it appears. Maintain formatting. Do not add conversational intro or outro text. Return pure extracted text."},
                    {
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": img_base64
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
             print(f"❌ [API FAULT] Connection rejected: {response.text}")
             return

        response_data = response.json()
        
        # Parse text from JSON structure safely
        try:
            extracted_text = response_data['candidates'][0]['content']['parts'][0]['text'].strip()
        except (KeyError, IndexError):
            extracted_text = None
        
        if extracted_text:
            pyperclip.copy(extracted_text)
            print("\n========================================================")
            print(extracted_text)
            print("========================================================")
            print("⚡ [CLIPBOARD MATRIX] Payload copied to Windows clipboard successfully.")
        else:
            print("⚠️ [SYSTEM WARNING] Canvas analysis yielded zero readable characters.")
            
    except Exception as e:
        print(f"❌ [CRITICAL FAULT] Vision Strike aborted: {str(e)}")
    finally:
        # Clean up local storage array immediately to keep memory lean
        if os.path.exists(RAW_IMAGE_PATH):
            os.remove(RAW_IMAGE_PATH)

if __name__ == "__main__":
    execute_vision_strike()