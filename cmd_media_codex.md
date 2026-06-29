# CMD MEDIA CODEX — OPERATIONAL KNOWLEDGE (v3)
> CMD Gem operating reference. Arif is the carrier between gems.
> Last updated: 2026-06-10

---

## 1. THE OPERATOR

Arif. Chennai. MBA student. Ex-Accenture. Pivoting to Startup Ops/CoS.
"Efficiency Over Mastery." Tried conventional YouTube 2 years, no results — does NOT want conventional advice repeated.

---

## 2. CHARACTER REFERENCE SYSTEM

- Protagonist: [TO BE FILLED]
- Art style prefix: [TO BE FILLED — paste locked Ideogram prefix]
- Character ref folder: `C:\neo_core\media\character_ref\protagonist\`
- Style prefix file: `C:\neo_core\media\character_ref\style_prefix.txt` — this file is injected into every Ideogram prompt. Edit here to change the locked style.
- **Rule:** every image prompt starts with the locked art style prefix.

---

## 3. CHANNEL MAP (v2)

| Ch | Account | Type | Monetization | Risk |
|----|---------|------|-------------|------|
| 1 Free Spirit | Account 1 | Anime/manga, educational, entertainment, LIGHT commentary | AdSense + Affiliate | Protected — keep clean |
| 2 Sensitive | Account 2 | Heavy commentary, sensitive/world topics, provocative | Affiliate ONLY (Alpha Base) | Quarantine — demonetization expected, NEVER a strike |
| 3 Authority | Account 3 | NEO demos, B2B | B2B leads | Clean |

Converter = unlisted videos, no channel.

---

## 4. THE TWO PENALTIES (drill this)

- **Demonetization** = ad loss. Recoverable. Fine on Channel 2.
- **Strike/Termination** = Community Guidelines violation. 3 = channel deleted; severe = account. Quarantine does NOT protect against this. Channel 2 must stay controversial-but-COMPLIANT.

---

## 5. PLAYLISTS

**Channel 1 (Free Spirit):**
- 📺 Anime & Manga Deep Dives
- 📚 Explained (educational)
- 🎭 Stories & Entertainment
- 💡 Light Takes (safe commentary)

**Channel 2 (Sensitive):**
- 🌍 World Commentary
- ⚖️ What If (hypotheticals)
- 🔥 Hard Questions

**Channel 3 (Authority):**
- ⚙️ NEO in Action
- 🛠️ Systems & Automation

---

## 6. TAG STRATEGY

10-15 tags/video: 3-4 topic-specific + 3-4 niche + 2-3 broad + 1-2 hook. CMD always generates.

---

## 7. UPLOAD PROTOCOL

- Channels 1 & 2: "Do not notify subscribers." Playlist-organized.
- Bio (Ch1): "I post anything worth watching. Explore the playlists 👇"
- Bio (Ch2): "Uncomfortable questions, honestly asked. Playlists 👇"
- Every description: 2-line summary + playlist link + Alpha Base link.
- Thumbnail: high contrast, ≤5 words, curiosity gap.

---

## 8. ALPHA BASE INTEGRATION

- Alpha Base URL: [paste when live]
- Every Ch1 + Ch2 description ends with: "Tools I use → [Alpha Base URL]"
- Tool-related videos: specific affiliate links above the Alpha Base link.

---

## 9. NEO MEDIA PIPELINE STATUS

- [✅ BUILT] `image_prompt_batcher.py` — script .txt → numbered Ideogram prompts, locked style prefix from style_prefix.txt injected into each. Groq parse (openai/gpt-oss-120b). Output: media/assets/<video_id>/prompts.txt + prompts_numbered.txt
- [ ] `video_forge.py` — TTS + MoviePy assembly
- [ ] `cmd_router.py` — parses `[NEO_MEDIA_BUILD]` tags

Update when NEO Architect sends `[NEO_STATUS_UPDATE]`.

---

## 10. CONTENT PIPELINE STATUS

- Scripts queue: [titles]
- Assets generated: [per video_id]
- Uploaded: [per video_id + channel]

---

## 11. REVENUE TRACK — CURRENT STATUS

| Item | Status |
|------|--------|
| Reddit Bounty Tracker | ✅ LIVE — `reddit_bounty_tracker.py` |
| Fiverr Gig | ✅ LIVE — Data > Data Processing > Automations |
| Revenue secured | ₹0 (0 gigs closed as of 2026-06-09) |
| Liquidity target | ₹14,000 this month |
| Primary close channel | Reddit [Hiring] replies (demand-first) |

---

## 12. LIVE TOOLS (Revenue Track)

### `reddit_bounty_tracker.py` — Root level
Polls 13 freelance subreddits via RSS. Zero credentials. Fires toast, opens browser, logs to `bounty_log.csv`.

**Blacklist gates (auto-drop):** geo (EU/LATAM/US/UK-only) · commission/success-fee/referral · onsite/WFO · VA roles without technical keywords · hybrid paired with full-time/office.

**Operator action when bounty fires:** URL auto-opens → read post → paste reply template.

### `neo/tools/content_validator.py`
Pre-save validation gate for all scrapers. Import on every scraper build:
```python
from neo.tools.content_validator import validate_pricing_doc, validate_pricing_text, rank_candidates
if not validate_pricing_doc(resp.content, entity_name): continue
if not validate_pricing_text(page_text, entity_name): continue
```
A job was lost to blind ingestion. This is the permanent fix.

---

## 13. OUTREACH PROTOCOL

### Channel Priority
| # | Channel | Notes |
|---|---------|-------|
| 1 | Reddit tracker hits (auto-surface) | Reply immediately |
| 2 | Manual r/forhire / r/freelance_forhire browse | Sort by New |
| 3 | Fiverr inbound | Passive |
| 4 | Discord #for-hire (manual) | Post in 6-8 channels |
| 5 | Cold email — slow track only | See hard stops |

### Reddit Reply Template
```
Hey — I can handle this. I build Python automation for data extraction,
cleaning, and lead list building. Flat rate, 24-48hr turnaround.

To prove it: send me your site URL or CSV and I'll return the first 50 rows
cleaned/extracted today, free. If the output beats your current process,
we scope the full job.

What's the source you need pulled?
```

### Cold Email Template (validated lists only — never personal Gmail)
```
Subject: Data extraction / manual entry bottleneck

Hi [First Name],

If your team pays manual VAs to copy-paste leads, fix messy CSVs, or format
CRM data, you're bleeding margin. I extract and clean data at machine-velocity,
flat rates.

Basic: 1 site or 500 rows ($30) | Standard: up to 5k rows deduped ($75)

Reply with a URL or CSV — I'll send you the first 50 rows free today.

Best, Arif
```

---

## 14. PRICING

| Tier | Scope | Price |
|------|-------|-------|
| Basic | 1 site, ≤500 rows | $30 / ₹2.5k |
| Standard | Multi-page, ≤5k rows, deduped | $75 / ₹6.5k |
| Premium | Full site + scheduled refresh | $150 / ₹13k |

---

## 15. FIVERR GIG METADATA

| Field | Value |
|-------|-------|
| Category | Data |
| Subcategory | Data Processing |
| Service Type | Automations |
| Technology (5) | Microsoft Excel · Google Sheets · Python · Pandas · SQL |
| Expertise (8) | Data extraction · Data acquisition · Data manipulation · Normalization · Transformation · Data validation · ETL · Data flow |
| Tags (5) | data cleaning · data extraction · web scraping · excel formatting · lead list building |
| Note | First published title is permanent in URL — use keywords before publishing |

---

## 16. PLATFORM HARD STOPS

| Platform | Status | Risk |
|----------|--------|------|
| Gmail SMTP cold email | ⛔ BLOCKED | Full Google account suspension |
| LinkedIn automation (logged-in) | ⛔ BLOCKED | Permanent LI ban — CoS career asset |
| Facebook automation (logged-in) | ⛔ BLOCKED | Real account ban |
| Reddit JSON API | ❌ DEAD | Killed Dec 2025. RSS only. |
| Clutch.co scraping | ⚠️ HIGH RISK | Cloudflare-hardened; build cost vs deadline |
| SMTP VRFY/RCPT probing | ⚠️ USELESS | Catch-alls return false positives; IP greylisted |

---

## 17. ZERO-NOISE SCRAPER PROTOCOL (CMD reference)

When sending a `[NEO_BUILD_REQUEST]` for a scraper, always include:
- WHITELIST: anchor/URL keywords that must be present
- BLACKLIST: anchor/URL keywords that skip instantly
- Entity name for content_validator relevance check

NEO auto-applies: block CSS/images/media (never scripts), rank candidates best-first, validate before save, batch-export via csv.writer.

---

## 18. HUMAN-IN-THE-LOOP RULE

NEO finds targets → Arif approves → NEO executes send.
Never bypass manual review. Automated sending = false positives + spam flags + account burns.

---

## 19. NEXT ACTIONS

| Priority | Action |
|----------|--------|
| 1 | Reply to Reddit [Hiring] posts surfaced by tracker |
| 2 | Monitor Fiverr for first order |
| 3 | `image_prompt_batcher.py` — unblocks daily YT production |
| 4 | `video_forge.py` — after image_prompt_batcher |
| 5 | `email_validator.py` (MX + regex) — build when a client list job lands |

---

## 20. SCRIPT GENERATION PROTOCOL

### Voice Guardrails (mandatory on every script prompt)
- **Client type:** active operator, not course seller
- **BANNED words/phrases:** "download", "free template", "join our community",
  "link in bio", "DM me", "comment for access", "enroll", "course", "program"
- **CTA format:** tease next video only — reference a specific real event/deal/number
- **Tone:** street-level, first-person operator. Zero guru energy.

### Groq Prompt Sibling Rule
When building the script generator module (sibling to `image_prompt_batcher.py`), the Groq prompt **must** include this exact line:

```python
"NEVER use course-seller CTA language. End with a specific next-video tease only."
```

This line is non-negotiable. It enforces the Voice Guardrails CTA format and tone at the LLM prompt level.

---

## 21. WHAT NEO CAN DELIVER RIGHT NOW (revenue-ready)
- **Faceless Shorts (30 = $150–200):** TTS (edge-tts) + captions + static B-roll assembly via MoviePy. Deliverable to clients now.
- **Script generation:** Groq openai/gpt-oss-120b. Wholesaling, real estate, faceless YouTube.

Hard limits (8GB rig — do NOT request beyond these):
- No AI-generated backgrounds (too compute-heavy)
- No beat-synced / VFX-heavy edits — manual CapCut only
- No copyrighted sports/broadcast footage (strike risk)
- MoviePy: single-thread, static B-roll pipeline only

---

## 22. GROQ MODEL (correct string — use this everywhere)
openai/gpt-oss-120b
⚠️ llama3-70b-8192 is DEPRECATED — will throw errors.

---

## 23. VOICE GUARDRAILS (inject into every script prompt)
BANNED WORDS: "download", "free template", "join our community", "link in bio",
"DM me", "comment for access", "enroll", "course", "program"
CTA format: tease next video with a specific real event/deal/number only.
Tone: street-level operator, first-person. Zero guru energy.

---

## 24. CLIENT PIPELINE LOG
- wholesaling scripts × 2 → delivered (ahmed.billion16@icloud.com) ✅
- Money-Let-9868: pitched faceless Shorts PoC (Zlatan kinetic typography format) — awaiting validation

---

*Last updated: 2026-06-11*