"""
neo/tools/filesystem.py
=======================
Handles all local file reading, writing, web searching, and browser interaction.
"""
import os
import sys
import glob
import shutil
import subprocess
import webbrowser
import urllib.request
import pyperclip

def create_file(path: str, content: str) -> str:
    """Creates a new file with the given content."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if os.path.exists(path):
        return f"Error: File '{path}' already exists. Use edit_file or write_file instead."
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Created: {path}"

def write_file(path: str, content: str) -> str:
    """Overwrites a file with new content."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"✅ Written to: {path}"

def read_file(path: str) -> str:
    """Reads the contents of a file."""
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replaces a specific string in a file with a new string."""
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    if old_text not in content:
        return f"Error: Could not find exactly '{old_text}' in {path}."
        
    # Save a backup before editing
    shutil.copy(path, path + ".bak")
    
    new_content = content.replace(old_text, new_text, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    return f"✅ Edited: {path} (backup saved as {path}.bak)"

def delete_file(path: str) -> str:
    """Moves a file to the .neo_trash folder instead of permanent deletion."""
    if not os.path.exists(path):
        return f"Error: File not found: {path}"
        
    trash_dir = ".neo_trash"
    os.makedirs(trash_dir, exist_ok=True)
    
    import time
    filename = os.path.basename(path)
    trash_path = os.path.join(trash_dir, f"{filename}.{int(time.time())}")
    
    shutil.move(path, trash_path)
    return f"✅ Deleted (recoverable): {path} → {trash_path}"

def list_files(directory: str = ".", pattern: str = "*") -> str:
    """Lists files in a directory matching a pattern."""
    if not os.path.exists(directory):
        return f"Error: Directory not found: {directory}"
        
    search_path = os.path.join(directory, pattern)
    files = glob.glob(search_path)
    
    if not files:
        return "No files found."
        
    output = []
    for f in files:
        if os.path.isfile(f):
            size = os.path.getsize(f)
            output.append(f"{os.path.basename(f)} ({size} bytes)")
    return "\n".join(output)

def open_website(url: str) -> str:
    """Opens a website URL or local HTML file in the default browser."""
    # If Neo is trying to open a local file
    if url.endswith(".html") or url.startswith("file:"):
        # Strip out any hallucinated 'file://' formatting
        clean_path = url.replace("file:///", "").replace("file://", "").replace("file:/", "")
        # Resolve the real absolute path (OS-agnostic)
        full_path = os.path.abspath(clean_path)
        # Convert it to a proper file:// URI (e.g. file:///home/user/page.html)
        url = urllib.request.pathname2url(full_path)
        # Ensure it starts with the correct file prefix
        if not url.startswith("file:"):
            url = "file:" + url
            
    # Otherwise, ensure regular websites have https://
    elif not url.startswith("http"):
        url = "https://" + url
        
    webbrowser.open(url)
    return f"✅ Opened {url} in the browser."

def search_web(query: str) -> str:
    """Searches the web and returns the top 5 results with descriptions and links."""
    try:
        from ddgs import DDGS
        results = DDGS().text(query, max_results=5)
        if not results:
            return "No results found."
        
        formatted = []
        for r in results:
            formatted.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nLink: {r.get('href')}\n")
        return "\n".join(formatted)
    except Exception as e:
        return f"Error searching the web: {e}"

def ask_gemini_web(massive_prompt: str) -> str:
    """Copies massive context to the clipboard, opens Gemini, and waits for user."""
    pyperclip.copy(massive_prompt)
    webbrowser.open("https://gemini.google.com/app")
    
    # Pauses the Python script until you press Enter in the terminal
    input("\n[System] 🛑 I have copied the prompt and opened Gemini.\nPaste the prompt (Ctrl+V), wait for the AI to answer, then press ENTER in this terminal to let me read the screen...")
    
    return "✅ User confirmed the answer is generated. You can now use read_screen() to capture the response."

def open_local_file(path: str) -> str:
    """Opens a file on the user's screen with their default application."""
    if not os.path.exists(path):
        return f"❌ Failed to open file: {path} does not exist."
    try:
        # Cross-platform replacement for Windows' os.startfile(): xdg-open on
        # Linux, open on macOS, start on Windows. Detached so Neo isn't blocked.
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path], start_new_session=True)
        else:
            subprocess.Popen(
                ["xdg-open", path],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return f"✅ Popped open '{path}' on the screen."
    except Exception as e:
        return f"❌ Failed to open file: {e}"

def read_pdf(path: str) -> str:
    """Reads and extracts all text from a PDF document."""
    try:
        from pypdf import PdfReader
        text = ""
        with open(path, "rb") as f:
            reader = PdfReader(f)
            # Read all pages and combine the text
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
        if not text.strip():
            return f"❌ Successfully opened PDF, but no readable text was found (it might be a scanned image)."
            
        # Return the text (capped at 50,000 characters to prevent crashing the LLM's memory)
        return text[:50000]
    except Exception as e:
        return f"❌ Failed to read PDF: {e}"

def analyze_image(image_path: str, prompt: str) -> str:
    """
    Groq Vision Matrix - With Auto-Compression Pipeline.
    Shrinks payload to bypass the 4MB Base64 crash limit.
    """
    import os
    import base64
    from io import BytesIO
    from PIL import Image
    try:
        from groq import Groq
    except ImportError:
        return "❌ MISSING DEPENDENCY: RUN 'pip install groq'"

    try:
        # Check your Windows Environment Variables. It MUST be spelled GROQ_API_KEY.
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            return "❌ API KEY MISSING. CHECK ENV VARIABLES."

        client = Groq(api_key=groq_key)

        # 1. Image Compression Pipeline (Bypass 4MB Limit)
        img = Image.open(image_path)
        
        # Strip alpha channel (transparency) which crashes vision models
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Shrink the image resolution to ensure it never exceeds Groq's 4MB limit
        img.thumbnail((1280, 720), Image.Resampling.LANCZOS)
        
        # Save to a temporary memory buffer as a lightweight JPEG
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=80)
        base64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')

        print("\n[VISION STRIKE] Uploading compressed payload to Groq...")

        # 2. Fire the optimized payload
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                            },
                        },
                    ],
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.1, # Highly logical setting for data extraction
            max_tokens=2048
        )
        
        print("\n[VISION STRIKE] Successful Extraction.")
        return chat_completion.choices[0].message.content

    except Exception as e:
        error_str = str(e)
        # We print to terminal so you can see exactly what Groq is complaining about
        print(f"\n[CRITICAL GROQ FAULT] RAW ERROR:\n{error_str}\n")
        return f"❌ GROQ VISION FAULT: {error_str}"

def headless_osint_scrape(url: str) -> str:
    """
    Lightweight web scraper optimized for 8GB RAM.
    Rotates browser footprints and headers dynamically to evade basic anti-bot blocks.
    """
    import requests
    import random
    from bs4 import BeautifulSoup

    # Dynamic User-Agent Pool to rotate device profiles
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ]

    # Advanced header blueprint to mimic a natural organic session
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://www.google.com/",
        "DNT": "1",  # Do Not Track request flag
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        # Use a session context manager to persist cookie compliance automatically
        with requests.Session() as session:
            response = session.get(url, headers=headers, timeout=12)
            
            if response.status_code == 429:
                return "❌ TARGET SERVER LIMIT BREACHED (429). INITIATING RADAR COOLDOWN."
            elif response.status_code == 403:
                return "❌ ACCESS FORBIDDEN (403). STEALTH MATRIX DEFECTIVE FOR THIS DOMAIN."
            elif response.status_code != 200:
                return f"❌ HTTP FAULT: STATUS CODE {response.status_code}"
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Pure signal extraction: purge code clutter
            for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                element.extract()
                
            pure_text = soup.get_text(separator=' ', strip=True)
            return pure_text[:35000] # Safe token roof for processing

    except Exception as e:
        return f"❌ STEALTH SCRAPER CRITICAL ERR: {str(e)}"

def chunk_document_payload(text: str, max_chars_per_chunk: int = 12000, overlap: int = 1500) -> list:
    """
    Slices large data text arrays into logical structural chunks.
    Prevents API context exhaustion and thrashing on 8GB local RAM systems.
    """
    if len(text) <= max_chars_per_chunk:
        return [text]
        
    chunks = []
    start_idx = 0
    total_length = len(text)
    
    while start_idx < total_length:
        end_idx = start_idx + max_chars_per_chunk
        
        # Pull chunk slice
        chunk = text[start_idx:end_idx]
        chunks.append(chunk)
        
        # Increment with sliding overlap to maintain semantic context boundaries
        start_idx += (max_chars_per_chunk - overlap)
        
    return chunks
