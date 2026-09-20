import pandas as pd
from pathlib import Path

# Load both files
structured  = pd.read_csv("CA_Structured_Pricing_Final.csv", encoding="utf-8")
original    = pd.read_csv("ca_pricing_delivery.csv", encoding="utf-8")

# Recover dropped rows (had PDF but no pricing text - still deliverable)
original_yes = original[original["Pricing Found"] == "Yes"].copy()
structured_names = set(structured["Venue Name"].str.lower().str.strip())
dropped = original_yes[
    ~original_yes["Venue Name"].str.lower().str.strip().isin(structured_names)
].copy()
dropped["Base_Price"] = None
dropped["Max_Price"]  = None
dropped["Currency"]   = None
dropped = dropped.drop(columns=["Pricing Text"], errors="ignore")
print(f"Recovered {len(dropped)} dropped rows (PDF-only)")

# Merge back
combined = pd.concat([structured, dropped], ignore_index=True)

# Filter junk prices (venue prices are never < $100 as a flat rate)
# Keep rows where Base_Price is null (might have PDF) or >= 100
price_mask = combined["Base_Price"].isna() | (combined["Base_Price"] >= 100)
combined   = combined[price_mask].copy()

# Filter out rows with no pricing AND no PDF
has_price = combined["Base_Price"].notna()
has_pdf   = combined["PDF File"].notna() & combined["PDF File"].ne("")
combined  = combined[has_price | has_pdf].copy()

# Fix bad venue name (URL as name)
combined = combined[~combined["Venue Name"].str.startswith("http")]

# Count deliverables
has_price_count = combined["Base_Price"].notna().sum()
has_pdf_count   = combined["PDF File"].notna().sum()
total           = len(combined)

# Save
combined.to_csv("CA_Final_Delivery.csv", index=False, encoding="utf-8")

print(f"\n📊 CA Final Delivery Summary:")
print(f"   Total deliverable rows : {total}")
print(f"   With structured prices : {has_price_count}")
print(f"   With PDF attached      : {has_pdf_count}")
print(f"   → CA_Final_Delivery.csv")

# Also list actual PDF files on disk
pdf_dir   = Path("downloads/pdfs/ca_pricing")
pdf_files = list(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
print(f"\n📁 PDFs on disk: {len(pdf_files)}")
for f in pdf_files[:10]:
    print(f"   {f.name}")
if len(pdf_files) > 10:
    print(f"   ...and {len(pdf_files)-10} more")
