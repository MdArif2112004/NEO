"""
content_validator.py — NEO Scraper Validation Gate
Stops blind ingestion. Validates that a downloaded file OR a scraped page
actually contains pricing AND relates to the right venue, BEFORE saving.
Prevents the "right name, wrong content" failure that loses jobs.

RAM cost: low. pypdf is pure-python; we read only the first 5 pages.
Dependency: pypdf  ->  pip install pypdf   (do NOT use pdfplumber — heavy)

Location: neo/tools/content_validator.py

Usage in any scraper:
    from neo.tools.content_validator import (
        validate_pricing_doc, validate_pricing_text, rank_candidates
    )

    # A downloaded PDF:
    if not validate_pricing_doc(resp.content, venue_name):
        continue                      # junk -> skip, never save

    # Pricing shown on the webpage itself (no PDF):
    if not validate_pricing_text(page_text, venue_name):
        continue
"""

import io
import re

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None   # validate_pricing_doc fails safe -> rejects everything

# ── Tunables (adjust per job) ──────────────────────────────────────────────

# What "looks like pricing"
PRICING_SIGNALS = re.compile(
    r"(\$|₹|£|€|\bper person\b|\bper head\b|\bpackage\b|"
    r"\bstarting at\b|\brate\b|\bpricing\b|\b\d{3,6}\b)",
    re.I,
)

MIN_SIGNALS = 3            # need at least this many pricing hits
MIN_BYTES   = 3_000        # smaller = probably an error/placeholder page
MAX_BYTES   = 15_000_000   # bigger = RAM risk on 8GB -> skip
MAX_PAGES   = 5            # only read first N pages to validate

# ── Internals ──────────────────────────────────────────────────────────────

def _has_pricing(text: str) -> bool:
    return len(PRICING_SIGNALS.findall(text or "")) >= MIN_SIGNALS

def _is_relevant(text: str, entity_name: str) -> bool:
    """First word of the venue name must appear in the content."""
    if not entity_name:
        return True   # no name supplied -> skip relevance check
    token = entity_name.lower().split()[0]
    return token in (text or "").lower()

# ── Public gates ─────────────────────────────────────────────────────────────

def validate_pricing_doc(raw_bytes: bytes, entity_name: str = "") -> bool:
    """True only if raw_bytes is a real PDF that looks like pricing for this venue."""
    if PdfReader is None:
        return False
    if not raw_bytes.startswith(b"%PDF"):              # real PDF, not HTML-as-.pdf
        return False
    if not (MIN_BYTES < len(raw_bytes) < MAX_BYTES):   # size sanity (protects RAM)
        return False
    try:
        reader = PdfReader(io.BytesIO(raw_bytes))
        text = " ".join((p.extract_text() or "") for p in reader.pages[:MAX_PAGES])
    except Exception:
        return False
    return _has_pricing(text) and _is_relevant(text, entity_name)

def validate_pricing_text(text: str, entity_name: str = "") -> bool:
    """For pricing shown directly on a webpage (HTML text you scraped, not a file)."""
    if not text or len(text) < 50:
        return False
    return _has_pricing(text) and _is_relevant(text, entity_name)

def rank_candidates(links: list[dict]) -> list[dict]:
    """
    Sort links best-first so you try the strongest match before the weak ones.
    links: [{'url': str, 'anchor': str}, ...]
    """
    def score(link):
        a = (link.get("anchor") or "").lower()
        u = (link.get("url") or "").lower()
        s = 0
        if "pricing" in a or "pricing" in u: s += 3
        if "price" in a or "price" in u:     s += 2
        if "rate" in a or "rate" in u:       s += 2
        if u.endswith(".pdf"):               s += 1
        return s
    return sorted(links, key=score, reverse=True)
