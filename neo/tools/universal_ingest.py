"""
neo/tools/universal_ingest.py
=============================
Universal Data Ingestion Engine for B2B Freelance Tasks.
Extracts text from PDF/TXT/CSV, chunks it, enforces JSON output via Groq Llama 3, 
and streams directly to a local CSV. 8GB RAM optimized.
"""
import os
import json
import csv
from groq import Groq

def get_text_from_pdf(filepath):
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(filepath)
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        return text
    except ImportError:
        return "❌ PyMuPDF not installed. Run: pip install PyMuPDF"

def get_text_from_file(filepath):
    ext = filepath.split('.')[-1].lower()
    if ext == 'pdf':
        return get_text_from_pdf(filepath)
    elif ext in ['txt', 'csv']:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    else:
        return f"❌ Unsupported file type: {ext}"

def chunk_text(text, chunk_size=15000):
    # 15,000 chars is roughly 3,500 tokens. 
    # Leaves plenty of buffer room for Groq's 8k token limit.
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def run_ingestion_pipeline(filepath: str, extraction_goal: str, output_csv="output.csv") -> str:
    """
    Reads a file, chunks it, queries Groq for strict JSON based on the extraction_goal,
    and appends the results to a CSV.
    """
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return "❌ GROQ_API_KEY missing from environment variables."

    client = Groq(api_key=groq_key)
    
    print(f"\n[INGESTION] Reading file: {filepath}")
    raw_text = get_text_from_file(filepath)
    if raw_text.startswith("❌"):
        return raw_text

    chunks = chunk_text(raw_text)
    print(f"[INGESTION] Payload chunked into {len(chunks)} blocks to protect RAM.\n")

    # The strict JSON lock protocol
    system_prompt = (
        "You are a strictly constrained data extraction terminal. "
        "Extract the requested data from the provided text. "
        "You MUST output valid JSON ONLY. No markdown, no conversational text. "
        "Output format: {\"data\": [{\"field1\": \"value1\", \"field2\": \"value2\"}]}"
    )

    total_extracted = 0

    for idx, chunk in enumerate(chunks):
        print(f"  -> Processing Chunk {idx+1}/{len(chunks)} via Groq Llama 3...")
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extraction Goal: {extraction_goal}\n\nText:\n{chunk}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.1 # Low temperature for extreme analytical accuracy
            )
            
            result_text = response.choices[0].message.content
            data_dict = json.loads(result_text)
            
            rows = data_dict.get("data", [])
            if not rows:
                continue
                
            # Stream directly to CSV to prevent memory bloat
            file_exists = os.path.isfile(output_csv)
            with open(output_csv, 'a', newline='', encoding='utf-8') as f:
                # Use the keys from the first parsed dictionary as headers
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                if not file_exists:
                    writer.writeheader()
                for row in rows:
                    writer.writerow(row)
                    total_extracted += 1

        except Exception as e:
            print(f"  ❌ Chunk {idx+1} Error: {str(e)}")
            continue

    return f"✅ INGESTION COMPLETE: {total_extracted} records cleanly extracted to {output_csv}."
