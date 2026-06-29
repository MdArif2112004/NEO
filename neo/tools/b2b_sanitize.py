"""
b2b_sanitize.py — Cut a clean deliverable from enriched CSV
============================================================
Steps:
  1. Drop true-NaN emails (pandas 3.x safe — dropna FIRST)
  2. Drop blank / placeholder / junk string emails
  3. MX-record check — drops domains with no mail server (hard bounces)
  4. Domain-mismatch flag — warns when email domain != company site domain
  5. Dedupe by email + by company name
  6. Prefer rows with websites (most complete first)
  7. Slice top N

Run:
  python neo/tools/b2b_sanitize.py [target_count] [--no-mx]

  --no-mx  : skip DNS lookups (faster, but won't catch dead domains)

Output: B2B_HR_Leads_PoC.csv

Dependencies: pandas, dnspython (pip install dnspython)
"""

import sys
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

ENRICHED = Path("B2B_HR_Leads_Enriched.csv")
OUTPUT   = Path("B2B_HR_Leads_PoC.csv")
TARGET   = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].lstrip('-').isdigit() else 50
NO_MX    = "--no-mx" in sys.argv or not DNS_AVAILABLE

VERSION_RE   = re.compile(r"@[\d]+\.[\d]")
CSS_RE       = re.compile(r"@\d+\.\.")
JUNK_DOMAINS = {"example.com", "domain.com", "example.org", "test.com",
                "placeholder.com", "email.com"}
JUNK_LOCAL   = {"noreply","no-reply","donotreply","support","admin",
                "spam","newsletter","abuse","postmaster","mailer","bounce",
                "unsubscribe","billing","notifications","alerts","example",
                "careers","jobs","test"}
# Sites that commonly appear as false enrichment matches
SKIP_SITES   = {"nintendo.com","toptal.com","trustpilot.com","remote.com",
                "glassdoor.com","indeed.com","linkedin.com","crunchbase.com"}

# ── Junk email filter ──────────────────────────────────────────────────────────

def is_junk_email(email: str) -> bool:
    e = str(email).strip().rstrip(".")
    if "@" not in e:
        return True
    local  = e.split("@")[0].lower()
    domain = e.split("@")[-1].lower()
    if VERSION_RE.search(e): return True      # npm: lenis@1.3.8
    if CSS_RE.search(e):     return True      # css: wght@100..900
    if domain in JUNK_DOMAINS: return True    # placeholder domains
    if any(j in local for j in JUNK_LOCAL): return True
    if len(e) > 80 or " " in e: return True
    return False

# ── Domain mismatch check (flag only, not hard drop) ─────────────────────────

def domain_mismatch(email: str, website: str) -> bool:
    """Returns True if email domain is clearly unrelated to the company website."""
    if not website or not email:
        return False
    try:
        email_domain  = email.split("@")[-1].lower()
        site_domain   = (website.replace("https://www.","")
                                .replace("http://www.","")
                                .split("/")[0].lower())
        # Check if either root name appears in the other
        email_root = email_domain.split(".")[0]
        site_root  = site_domain.split(".")[0]
        if email_root in site_root or site_root in email_root:
            return False
        # Flag it
        return True
    except Exception:
        return False

# ── MX validation ─────────────────────────────────────────────────────────────

def check_mx(email: str) -> bool:
    """Returns True if the email's domain has valid MX records."""
    try:
        domain = email.split("@")[-1]
        records = dns.resolver.resolve(domain, "MX", lifetime=5)
        return bool(records)
    except Exception:
        return False

def bulk_mx_check(emails: list[str]) -> dict[str, bool]:
    """Parallel MX checks — 8GB safe, capped at 10 threads."""
    results = {}
    print(f"  Running MX checks on {len(emails)} domains (parallel, ~10s)...")
    with ThreadPoolExecutor(max_workers=10) as ex:
        future_to_email = {ex.submit(check_mx, e): e for e in emails}
        for future in as_completed(future_to_email):
            email = future_to_email[future]
            try:
                results[email] = future.result()
            except Exception:
                results[email] = False
    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not ENRICHED.exists():
        print(f"Not found: {ENRICHED}. Run b2b_enrich.py first.")
        return

    df = pd.read_csv(ENRICHED)
    before = len(df)

    # Step 1: Drop true NaN (pandas 3.x safe — MUST come before string ops)
    df = df.dropna(subset=["Email"])

    # Step 2: String normalise + junk filter
    df["Email"] = df["Email"].astype(str).str.strip().str.rstrip(".").str.lower()
    df = df[~df["Email"].apply(is_junk_email)]

    # Step 3: Drop wrong-site rows (website domain in skip list)
    if "Website" in df.columns:
        df["_site"] = df["Website"].astype(str).str.replace("https://www.","",regex=False)\
                                   .str.split("/").str[0].str.lower()
        df = df[~df["_site"].isin(SKIP_SITES)]
        df = df.drop(columns=["_site"])

    # Step 4: MX validation (unless --no-mx)
    mx_dropped = 0
    if not NO_MX:
        mx_results = bulk_mx_check(df["Email"].tolist())
        df["_mx"] = df["Email"].map(mx_results)
        mx_dropped = (~df["_mx"]).sum()
        df = df[df["_mx"]].drop(columns=["_mx"])
        print(f"  MX check: dropped {mx_dropped} dead domains")
    else:
        print("  MX check: skipped (--no-mx)")

    # Step 5: Domain mismatch flag (warn, don't drop — reviewer decides)
    if "Website" in df.columns:
        df["_mismatch"] = df.apply(
            lambda r: domain_mismatch(r["Email"], r.get("Website","")), axis=1)
        mismatches = df[df["_mismatch"]][["Company Name","Website","Email"]]
        if len(mismatches):
            print(f"\n  ⚠️  {len(mismatches)} domain mismatches (kept — verify before sending):")
            for _, r in mismatches.iterrows():
                print(f"     {r['Company Name'][:30]:<30} email: {r['Email']}  site: {r.get('Website','')}")
        df = df.drop(columns=["_mismatch"])

    # Step 6: Dedupe
    df = df.drop_duplicates(subset=["Email"])
    df = df.drop_duplicates(subset=["Company Name"])

    # Step 7: Sort — rows with websites first
    if "Website" in df.columns:
        df["_has_site"] = df["Website"].astype(str).str.strip().ne("").astype(int)
        df = df.sort_values("_has_site", ascending=False).drop(columns="_has_site")

    # Step 8: Slice
    df_final = df.head(TARGET)
    df_final.to_csv(OUTPUT, index=False)

    print(f"\n{'='*56}")
    print(f"  Input  : {before:,} rows")
    print(f"  Output : {len(df_final)} pristine rows -> {OUTPUT}")
    print(f"  MX dead domains dropped: {mx_dropped}")
    if len(df_final) < TARGET:
        short = TARGET - len(df_final)
        print(f"\n  ⚠️  {short} short of {TARGET}.")
        print(f"  Scrape more names (raise MAX_RESULTS in b2b_hr_scraper.py)")
        print(f"  and re-run the full pipeline.")
    else:
        print(f"  ✅ Exactly {TARGET} rows. Ready to deliver.")
    print(f"{'='*56}")

if __name__ == "__main__":
    main()
