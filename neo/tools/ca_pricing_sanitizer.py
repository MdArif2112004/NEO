"""
ca_pricing_sanitizer.py
Groq LLM parser — extracts Base_Price, Max_Price, Currency
from raw scraped pricing text.
"""
import pandas as pd
import json
import time
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE  = "ca_pricing_delivery.csv"
OUTPUT_FILE = "CA_Structured_Pricing_Final.csv"
MODEL       = "openai/gpt-oss-120b"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a data extraction parser. 
Read the venue pricing text and extract pricing information.
Output ONLY valid JSON in exactly this format, no other text:
{"Base_Price": integer or null, "Max_Price": integer or null, "Currency": "USD" or null}
Rules:
- Extract the LOWEST mentioned price as Base_Price
- Extract the HIGHEST mentioned price as Max_Price  
- Do not include commas in numbers
- If only one price exists, put it in Base_Price, null in Max_Price
- Currency is almost always USD for US venues"""

def parse_price(text):
    """Call Groq and return parsed dict. Returns nulls on failure."""
    empty = {"Base_Price": None, "Max_Price": None, "Currency": None}
    if not text or pd.isna(text):
        return empty
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Text: {str(text)[:500]}"}
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=100
        )
        raw = resp.choices[0].message.content.strip()
        data = json.loads(raw)
        return {
            "Base_Price": data.get("Base_Price"),
            "Max_Price":  data.get("Max_Price"),
            "Currency":   data.get("Currency")
        }
    except json.JSONDecodeError:
        print(f"  ⚠️ Bad JSON: {raw[:80]}")
        return empty
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return empty

def main():
    df = pd.read_csv(INPUT_FILE, encoding="utf-8")
    print(f"Loaded {len(df)} rows from {INPUT_FILE}")

    # Filter to rows with actual pricing text
    mask = df["Pricing Found"].eq("Yes") & df["Pricing Text"].notna() & df["Pricing Text"].ne("")
    df_yes = df[mask].copy()
    print(f"Rows with pricing text: {len(df_yes)}\n")

    results = []
    for i, (idx, row) in enumerate(df_yes.iterrows()):
        text = row["Pricing Text"]
        print(f"[{i+1}/{len(df_yes)}] {row['Venue Name'][:40]}", end=" → ")

        parsed = parse_price(text)
        results.append({
            "idx":        idx,
            "Base_Price": parsed["Base_Price"],
            "Max_Price":  parsed["Max_Price"],
            "Currency":   parsed["Currency"]
        })

        bp = parsed["Base_Price"]
        mp = parsed["Max_Price"]
        print(f"${bp} – ${mp}" if bp else "null")

        time.sleep(1)  # Rate limit buffer

        # Handle 429 — retry with backoff
        # (Groq raises groq.RateLimitError)

    # Map results back to dataframe
    res_df = pd.DataFrame(results).set_index("idx")
    df_yes = df_yes.join(res_df)

    # Drop messy raw column
    df_yes = df_yes.drop(columns=["Pricing Text"])

    # Save
    df_yes.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
    filled = df_yes["Base_Price"].notna().sum()
    print(f"\n✅ Done. {filled}/{len(df_yes)} rows have structured prices.")
    print(f"   → {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
