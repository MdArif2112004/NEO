"""
reddit_bounty_tracker.py — NEO Triple-Stream Reddit Bounty Hunter (RSS edition)
Streams: JOB_BOARD (tech-matched freelance/gigs) · BASELINE_INCOME (any-skill,
2-10 day quick cash — nothing-to-do-with-the-tech gigs, for baseline income) ·
FOUNDER_SUB (Track A+ founding-ops, direct-founder posts).
Synced to: Job Search Gem (₹18k/40hr floor secured elsewhere, Track A+ priority,
r/startups + r/cofounder channels) and Freelance Strategist Gem (capability gate,
pricing matrix, RLHF/compliance guardrails) — both current as of this update.
Auth: NONE — Reddit RSS feeds, no credentials needed.
RAM: ~10-15MB
Dependencies: requests, feedparser, notify-py
Install: pip install requests feedparser notify-py
Run: python reddit_bounty_tracker.py
"""

import csv
import time
import webbrowser
import threading
import logging
import calendar
import random
from datetime import datetime
from pathlib import Path

import requests
import feedparser
from notifypy import Notify

# ── Config ────────────────────────────────────────────────────────────────────

JOB_SUBS = {
    "forhire", "freelance_forhire", "freelancer_hire", "ForHireFreelance",
    "Freelancers", "hireforgigs", "slavelabour", "DoneDirtCheap",
    "FreelanceIndia", "remotejobsfinders", "remoteworking",
    "UpworkOfficial", "LookingforJob",
    "creatorservices",
}
FOUNDER_SUBS  = {"startups", "cofounder"}   # ACTIVE — Track A+ founding-ops priority (Job Search Gem channel strategy)
ALL_SUBS      = list(JOB_SUBS | FOUNDER_SUBS)
JOB_TITLE_TAGS = ["[hiring]", "[task]"]   # legacy — kept for reference, replaced by TITLE_INCLUDE below
# Title must contain at least one of these (mirrors Reddit Exact Search: title:hiring OR title:"looking for")
TITLE_INCLUDE = ["hiring", "looking for"]
# Title must NOT contain any of these (mirrors NOT title:"for hire" AND NOT title:"hire me")
TITLE_EXCLUDE = ["for hire", "hire me"]

JOB_KEYWORDS = [
    "scrape", "data entry", "lead list", "web scraping", 
    "data pipeline", "lead generation", "data extraction", 
    "data cleaning", "csv", "spreadsheet", 
    "youtube automation", "faceless", "bulk video", "script writing",
    "chief of staff", "founder's associate", "operations manager", 
    "data operations", "startup ops", "notion", "workspace architecture",
    "b2b leads", "email finding", "email extraction", "lead enrichment",
]

FOUNDER_KEYWORDS = [
    "how to find leads", "automate crm", "data extraction", 
    "lead generation", "looking for freelancer", "find leads",
    "systems builder", "operations architecture",
    "first ops hire", "founding ops", "operations hire", "ops hire",
    "early-stage", "pre-seed", "seed-stage", "founding team",
]

# Track: Baseline Income — short-duration (2-10 day), SKILL-AGNOSTIC paid gigs.
# Priority: real cash now over tech-fit. Nothing to do with Arif's actual stack is fine —
# still passes the hard blacklists (geo/comp/onsite/compliance), just skips the tech-
# keyword requirement AND the soft VA-without-tech filter (see match_baseline below).
BASELINE_KEYWORDS = [
    "quick job", "quick task", "small task", "one-off", "one off", "one time job",
    "urgent", "asap", "need done today", "need this week", "short term",
    "few hours", "couple of hours", "few days", "this weekend", "temp job",
    "temporary", "1 day", "2 day", "3 day", "day turnaround", "fast turnaround",
]

# ── Blacklists (Triage Hotfix) ─────────────────────────────────────────────

# Hard geo drop — strictly region-locked posts
BLACKLIST_GEO = [
    "eu only", "europe only", "latam only", "uk only", "us only",
    "eu or latam", "eu/latam", "north america only", "us-based only",
    "must be in eu", "must be in us", "must be uk", "canada only",
    "australia only",
]

# Hard compensation drop
BLACKLIST_COMP = [
    "commission based", "commission only", "commission-based",
    "success fee", "equity only", "unpaid", "performance linked",
    "rev share only", "revenue share only", "no base pay",
    "percentage of every sale", "commission every time", "referral fee",
]

# Hard role drop — traditional admin VA without tech component
BLACKLIST_ROLE = [
    "calendar management", "administrative support",
    "email coordination", "email management",
    "female streamer", "cam model", "slim", "appearance criteria",
    
    # ── HOTFIX: Tech & Engineering Traps ──
    "react", "frontend", "full-stack", "full stack", "django", 
    "java", "spring boot", "app developer", "chatbot", 
    "software developer", "software engineer",
    
    # ── HOTFIX: Manual Editor Traps ──
    "after effects", "davinci resolve", "premiere pro", 
    "vfx", "cinematic", "gameplay",

    # ── HOTFIX: RLHF/Data-Annotation Compliance Trap ──
    # Freelance Gem §5: routing these through an LLM violates anti-cheat protocols —
    # permanent bans + pay clawbacks. Hard block, not a judgment call.
    "rlhf", "reinforcement learning from human feedback", "data annotation",
    "data labeling", "data labelling", "outlier.ai", "alignerr",
    "ai training data", "model training feedback",

    # ── HOTFIX: Personal/Creator Data Traps ──
    # Freelance Gem §2: CANNOT-DELIVER — personal scraping triggers DPDP/GDPR liability.
    "influencer emails", "creator emails", "social media handles",
    "scrape instagram", "scrape tiktok", "personal profiles",
    "product photography", "product imagery", "luxury product shoot",
]

# Soft role drop — VA/PA posts that DON'T also mention technical keywords
SOFT_BLACKLIST_ROLE = ["virtual assistant", "va role", "personal assistant"]

# Onsite traps — physical-presence requirement = not remote-viable
BLACKLIST_ONSITE = [
    "wfo", "work from office", "work-from-office", "work from the office",
    "on-site", "onsite", "in-office", "in office",
    "must relocate", "must be based in",
]

# ── Infra ─────────────────────────────────────────────────────────────────────

BOUNTY_LOG     = Path("bounty_log.csv")
POLL_INTERVAL  = 420     # 7 minutes between cycles (optimizes for 403 survival)
FETCH_DELAY    = 5       # seconds between per-sub fetches (polite; reduces 403 blocks)
TOAST_DURATION = 8
TOAST_COOLDOWN = 5       # increased to avoid WNDPROC collision

RSS_BASES = ["https://www.reddit.com", "https://old.reddit.com"]

HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
        "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    },
]

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("NEO.BOUNTY")

SCRIPT_START = time.time()

# ── Init ──────────────────────────────────────────────────────────────────────

def init_log():
    if not BOUNTY_LOG.exists():
        with open(BOUNTY_LOG, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                ["timestamp", "stream", "subreddit", "title", "url", "matched_keyword"]
            )

# ── Session ────────────────────────────────────────────────────────────────────

SESSION = requests.Session()
SESSION.get("https://www.reddit.com/", headers=random.choice(HEADERS_POOL), timeout=10)

# ── Fetch (RSS) ───────────────────────────────────────────────────────────────

_working_base = RSS_BASES[0]   # only switches on a network error, not rate-limits

def fetch_sub(subreddit: str):
    """list[dict] on success | 'RATELIMIT' on 403/429 | [] on network error."""
    global _working_base
    order = [_working_base] + [b for b in RSS_BASES if b != _working_base]
    for base in order:
        url = f"{base}/r/{subreddit}/new.rss?limit=50"
        headers = random.choice(HEADERS_POOL)
        try:
            r = SESSION.get(url, headers=headers, timeout=15)
            if r.status_code in (403, 429):
                log.warning(f"{r.status_code} [{subreddit}] — rate-limited")
                return "RATELIMIT"          # same limit on both bases — don't retry
            r.raise_for_status()
            feed = feedparser.parse(r.content)
            if feed.bozo and not feed.entries:
                continue
            _working_base = base
            return [{
                "id":    e.get("id", e.get("link", "")),
                "title": e.get("title", ""),
                "url":   e.get("link", ""),
                "body":  e.get("summary", ""),
                "sub":   subreddit,
                "ts":    calendar.timegm(e.published_parsed) if e.get("published_parsed") else 0,
            } for e in feed.entries]
        except requests.exceptions.RequestException as ex:
            log.error(f"Net error [{subreddit}] via {base}: {type(ex).__name__}")
            continue                         # network/DNS — try the other base once
    return []

# ── Blacklist Gate ─────────────────────────────────────────────────────────────

def _lower(text) -> str:
    return (text or "").lower()

def is_blacklisted(post: dict, check_soft_va: bool = True) -> bool:
    """check_soft_va=False skips the VA/PA-without-tech drop — used by the
    Baseline Income stream, which WANTS skill-agnostic quick gigs. All other
    checks (geo/comp/role/onsite/compliance) still apply regardless."""
    full = _lower(post.get("title", "")) + " " + _lower(post.get("body", ""))

    for kw in BLACKLIST_GEO:
        if kw in full:
            log.debug(f"GEO DROP [{post.get('sub')}]: {post.get('title', '')[:60]} | kw={kw!r}")
            return True

    for kw in BLACKLIST_COMP:
        if kw in full:
            log.debug(f"COMP DROP [{post.get('sub')}]: {post.get('title', '')[:60]} | kw={kw!r}")
            return True

    for kw in BLACKLIST_ROLE:
        if kw in full:
            log.debug(f"ROLE DROP [{post.get('sub')}]: {post.get('title', '')[:60]} | kw={kw!r}")
            return True

    # Onsite requirement = drop (achieves the no-non-Chennai-onsite goal
    # WITHOUT dropping remote gigs that merely mention a client's city)
    for kw in BLACKLIST_ONSITE:
        if kw in full:
            log.debug(f"ONSITE DROP [{post.get('sub')}]: {post.get('title', '')[:60]} | kw={kw!r}")
            return True

    # "hybrid" only in a work-arrangement context — protects "hybrid cloud" etc.
    if "hybrid" in full and any(t in full for t in ["full-time", "full time", "office", "wfo"]):
        log.debug(f"HYBRID DROP [{post.get('sub')}]: {post.get('title', '')[:60]}")
        return True

    # Soft: VA/PA posts without any technical keyword = drop (skippable — see docstring)
    if check_soft_va:
        has_soft = any(kw in full for kw in SOFT_BLACKLIST_ROLE)
        if has_soft:
            has_tech = any(kw in full for kw in JOB_KEYWORDS)
            if not has_tech:
                log.debug(f"VA DROP [{post.get('sub')}]: {post.get('title', '')[:60]}")
                return True

    return False

# ── Matching ──────────────────────────────────────────────────────────────────

def match_job(post: dict) -> str | None:
    if post["sub"].lower() not in {s.lower() for s in JOB_SUBS}:
        return None
    title = _lower(post["title"])
    # Reddit Exact Search: (title:hiring OR title:"looking for") AND NOT (title:"for hire" OR title:"hire me")
    if not any(inc in title for inc in TITLE_INCLUDE):
        return None
    if any(exc in title for exc in TITLE_EXCLUDE):
        return None
    if is_blacklisted(post):
        return None
    full = title + " " + _lower(post["body"])
    for kw in JOB_KEYWORDS:
        if kw in full:
            return kw
    return None

def match_baseline(post: dict) -> str | None:
    """Track: Baseline Income. Same subs as the job stream, but skill-agnostic —
    matches purely on a short-duration/urgency signal, not a tech keyword. This
    is the 'nothing to do with my tech, just need cash, 2-10 days' lane."""
    if post["sub"].lower() not in {s.lower() for s in JOB_SUBS}:
        return None
    title = _lower(post["title"])
    if not any(inc in title for inc in TITLE_INCLUDE):
        return None
    if any(exc in title for exc in TITLE_EXCLUDE):
        return None
    if is_blacklisted(post, check_soft_va=False):
        return None
    full = title + " " + _lower(post["body"])
    for kw in BASELINE_KEYWORDS:
        if kw in full:
            return kw
    return None

def match_founder(post: dict) -> str | None:
    if post["sub"].lower() not in {s.lower() for s in FOUNDER_SUBS}:
        return None
    if is_blacklisted(post):
        return None
    full = _lower(post["title"]) + " " + _lower(post["body"])
    for kw in FOUNDER_KEYWORDS:
        if kw in full:
            return kw
    return None

# ── Output ────────────────────────────────────────────────────────────────────

toaster     = Notify(default_notification_application_name="NEO")
_toast_lock = threading.Lock()

def fire_alert(post: dict, stream_label: str, keyword: str):
    sub_name  = post["sub"]
    post_url  = post["url"]
    title_str = post["title"][:80]

    log.info(f"BOUNTY [{stream_label}] r/{sub_name} | kw={keyword!r}")
    log.info(f"   Title : {title_str}")
    log.info(f"   URL   : {post_url}")

    def _toast():
        with _toast_lock:
            try:
                toaster.title   = f"NEO BOUNTY: {sub_name}"
                toaster.message = title_str
                toaster.urgency = "critical"
                # notify-py is non-blocking by default (it self-threads). The old
                # TOAST_DURATION is no longer honoured — the desktop owns expiry.
                toaster.send(block=False)
            except Exception:
                pass   # never let a toast failure kill the hunt loop
            time.sleep(TOAST_COOLDOWN)

    threading.Thread(target=_toast, daemon=True).start()
    webbrowser.open(post_url)

    with open(BOUNTY_LOG, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.utcnow().isoformat(timespec="seconds"),
            stream_label, sub_name, post["title"], post_url, keyword,
        ])

# ── Loop ──────────────────────────────────────────────────────────────────────

def run_loop():
    log.info(f"Watching {len(ALL_SUBS)} subs via RSS | poll={POLL_INTERVAL}s | delay={FETCH_DELAY}s/sub")
    log.info(f"Streams: JOB_BOARD (tech-match) + BASELINE_INCOME (any-skill, 2-10day) + FOUNDER_SUB (Track A+, {len(FOUNDER_SUBS)} subs: {', '.join(sorted(FOUNDER_SUBS))})")
    log.info(f"Blacklists active: geo={len(BLACKLIST_GEO)} | comp={len(BLACKLIST_COMP)} | role={len(BLACKLIST_ROLE)+len(SOFT_BLACKLIST_ROLE)}")
    log.info("Stream LIVE. Ctrl+C to stop.\n")

    seen        = set()
    cycle       = 0
    first_cycle = True

    while True:
        total       = 0
        hits        = 0
        dropped     = 0
        dead        = 0
        ratelimited = 0

        for sub in ALL_SUBS:
            result = fetch_sub(sub)
            if result == "RATELIMIT":
                ratelimited += 1
                posts = []
            elif not result:
                dead += 1
                posts = []
            else:
                posts = result
            time.sleep(random.uniform(8, 14))

            for post in posts:
                pid = post["id"]
                if pid in seen:
                    continue
                seen.add(pid)
                if first_cycle:
                    continue
                if post.get("ts") and post["ts"] < SCRIPT_START:
                    continue   # stale post resurfaced after a 403 gap — skip
                total += 1

                kw = match_job(post)
                if kw:
                    fire_alert(post, "JOB_BOARD", kw)
                    hits += 1
                    continue

                kw = match_baseline(post)
                if kw:
                    fire_alert(post, "BASELINE_INCOME", kw)
                    hits += 1
                    continue

                kw = match_founder(post)
                if kw:
                    fire_alert(post, "FOUNDER_SUB", kw)
                    hits += 1

        cycle += 1

        if first_cycle:
            status = "ALL DEAD — Reddit blocked" if dead == len(ALL_SUBS) else f"primed {len(seen)} posts ({dead} subs unreachable)"
            log.info(f"[cycle #1] {status}. Watching for NEW posts only.")
            first_cycle = False
        else:
            log.info(f"[cycle #{cycle}] new={total} | bounties={hits} | dead={dead} | rl={ratelimited} | seen={len(seen)}")

        if len(seen) > 8000:
            seen = set(list(seen)[-3000:])

        # Rate-limited? Back off hard instead of hammering every 5 min.
        if ratelimited >= max(3, len(ALL_SUBS) // 3):
            log.warning(f"Rate-limited on {ratelimited} subs — cooling down 15 min")
            time.sleep(900)
        else:
            time.sleep(POLL_INTERVAL)

# ── Entry ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_log()
    run_loop()