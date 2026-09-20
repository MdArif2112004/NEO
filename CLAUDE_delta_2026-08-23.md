# NEO — Session Delta (2026-08-23)

> Attach alongside CLAUDE.md. This file contains ONLY what is new, changed, or corrected
> since the last CLAUDE.md update (2026-06-16). On any conflict, this file wins.

---

## CHANGES TO EXISTING CLAUDE.md CONTENT

### 1. Failover chain (line 11 + line 125) — MODEL STRINGS OUTDATED
**Old (dead — decommissioned Aug 16 2026):**
```
Gemini 2.0 Flash → Groq (llama-3.3-70b-versatile) → Ollama (local Llama 3.2)
```
**New (current):**
```
Gemini 2.0 Flash → Groq (openai/gpt-oss-120b) → Ollama (local Llama 3.2)
```
Full migration completed repo-wide. Zero old strings remain. Verified clean via `findstr`.

### 2. Environment Variables (line 371) — NAME CORRECTIONS
`NOTION_API_KEY` is the correct Windows env var name (not `NOTION_DATABASE_ID`).
`NEO_TELEGRAM_TOKEN` is the correct name for Telegram (not `TELEGRAM_BOT_TOKEN`).
Cline introduced mismatches during the secret-removal pass; corrected in commit `a985624`.

**Corrected full list (Windows Environment Variables — not .env file):**
`GROQ_API_KEY` · `GEMINI_API_KEY` · `GEMINI_BACKUP_KEY` · `NOTION_API_KEY` ·
`DISCORD_BOT_TOKEN` · `DISCORD_WH_SYSTEM` · `DISCORD_WH_FACTORY` ·
`DISCORD_WH_OPERATOR` · `DISCORD_WH_CONVERTER` · `NEO_TELEGRAM_TOKEN` ·
`GMAIL_USER` · `GMAIL_APP_PASSWORD` (revoked — do not use) · `GROK_API_KEY` (typo duplicate of GROQ — delete it)

> **Important:** Secrets live in Windows Environment Variables, NOT a `.env` file.
> `os.getenv()` reads them directly. Restart terminal after any change.

### 3. wardialing_report.txt (line 100) — REMOVE FROM PUBLIC REPO
Excluded from GitHub via `.gitignore`. Name reads as unauthorized scanning to any hiring viewer. Never re-add to public repo.

### 4. Media Pipeline (line 428) — STATUS UPDATE
`neo/tools/video_forge.py` status changed from *(PLANNED)* to **PARTIALLY BUILT**.
A working `forge.py` (root level) was built this session:
- MoviePy 2.x syntax (not 1.x — breaking change)
- Edge-TTS voiceover
- 9:16 crop + 1080×1920 resize
- Captions deliberately OMITTED (ImageMagick build-trap — see Key Learnings)
- Takes ONE video clip for the full audio duration (no per-scene B-roll matching yet)
- Tested: 26.6s audio + 31.5s stock clip → `roman_pilot.mp4` rendered clean
- 8GB-safe: `threads=1`, `preset=ultrafast`, `codec=libx264`, `audio_codec=aac`

### 5. Key Learnings — 2 NEW ENTRIES (append to line 332)
```
- **Groq free-tier deprecation cycle (~30-day notice):** migrated off
  llama-3.3-70b-versatile (decommissioned Aug 16 2026) → openai/gpt-oss-120b;
  llama-3.1-8b-instant (Aug 16 2026) → openai/gpt-oss-20b in clip_ingest.py.
  New IDs carry a provider/ prefix (e.g. openai/, qwen/). gpt-oss-120b is a
  reasoning model — always set reasoning_effort="low" on JSON/structured calls
  or output format changes. ⚠️ Failover catches 429s but NOT 400
  model_decommissioned — a dead model string throws uncaught until manually swapped.

- **Voice mic — peak=1 = level, not permissions:** Vosk silence (capture peak ≈1)
  with mic access ON + "Currently in use" in taskbar means Realtek input volume
  slider at 0, NOT a Windows privacy block (that returns hard 0 / errors).
  Fix: Settings → Sound → Input → raise mic volume to 100.
  Working config: default device idx 1 (Microphone Realtek Audio), SAMPLE_RATE=16000.
```

### 6. Hardening Table — NEW ROW 15
```
| 15 | Groq model decommission | ✅ Migrated to gpt-oss-120b/20b repo-wide.
⚠️ Failover still 429-only — add model_decommissioned (400) error handling to
neo/llm/model.py to fully harden against future deprecations. ~5-line except block. |
```

---

## NEW CONTENT (not in CLAUDE.md at all)

### Operator Constraints (add to Binding Constraints)

```
- **Income-floor-first gate:** NEO builds restricted to revenue-critical only
  until a job or stable ₹20k/mo freelance is secured. Do NOT propose new features
  that pull toward building instead of applying/closing.
- **True Accenture record:** Arif was locked in Citrix/VDI at Accenture and could
  not deploy automation there. NEO and all automation was built outside work, on
  his own time. Never claim he automated at Accenture. Never list AutoHotkey on
  his resume.
- **Slow-down directive:** If Arif appears to be spiraling or rushing an
  irreversible decision, slow him down. Do not accelerate.
```

---

### Resume — Current State

**Status:** Send-ready for Founder's Associate, Growth Ops, BizOps, Automation/Internal-Tools roles.

**Key corrections applied this session:**
- Accenture section rewritten: no false automation claims; "Citrix/VDI" framing is honest and tactically better (preempts the "show me the Accenture automation" trap).
- AutoHotkey removed from Technical Stack.
- NEO section rewritten to lead with business outputs, not learning framing:
  - ReAct loop (Think → Act → Observe)
  - 3-tier LLM failover, 8GB RAM constraint framing
  - ~38 composable tools, Telegram/Discord remote control
- `MohammedArif2.11.2004@gmail.com` — email exposes birth year; flagged for change to plain firstname.lastname format.
- Make.com + NEO bullets risk reading as duplicate (both = scrape→DB). Keep Make.com = no-code/API-routing, NEO = autonomous Python agent.

---

### GitHub Repo — Public Portfolio Asset

**URL:** https://github.com/MdArif2112004/NEO

**Status:** Live, public, MIT licensed. Commit `a985624` — all secrets removed.

**Security passes completed:**
- `findstr` scan: caught + removed hardcoded `gsk_` Groq key (`neo/config.py`), Gemini key (`observer.py`), Notion tokens (3 files), Telegram token (`telegram_router.py`)
- All secrets now read via `os.getenv()` from Windows Environment Variables
- `.gitignore` blocks: `.env`, `*.csv`, `*.mp4/mp3/wav`, `models/`, `archive/`, `downloads/`, `__pycache__/`, `*.bak`, `*.key`
- MIT LICENSE added
- `wardialing_report.txt` excluded

**Keys rotated post-leak (do this if not done):**
- Groq → revoked old key, new key in Windows env
- Gemini → revoked old key, new key in Windows env
- Notion → rotate at notion.so/my-integrations (was in leaked first commit)
- Gmail app password → REVOKE permanently (myaccount.google.com → Security → App passwords). SMTP is a hard stop; this credential has no valid use.

**Open risk:** The first push (`9578975`) went up before Gemini + Notion keys were removed. Bots scrape public repos within minutes. Treat those keys as burned regardless of the force-push cleanup.

---

### Groq Model Migration — Full Record

| Old model | Decommission date | New model | Notes |
|---|---|---|---|
| `llama-3.3-70b-versatile` | Aug 16 2026 | `openai/gpt-oss-120b` | Primary reasoning. Add `reasoning_effort="low"` on JSON calls. |
| `llama-3.1-8b-instant` | Aug 16 2026 | `openai/gpt-oss-20b` | Only in `clip_ingest.py`. |

Files changed: 18 total (12 Python + 3 Markdown + 3 additional refs).
`reasoning_effort="low"` added to: `data_janitor.py` (line 224), `image_prompt_batcher.py` (line 68).
Runtime tested: `data_janitor` NL command + `image_prompt_batcher` JSON parse — both clean.

**Open risk (not yet fixed):** `neo/llm/model.py` failover catches `429` (rate limit) but NOT `400 model_decommissioned`. Next deprecation will throw uncaught until manually swapped. Fix = ~5-line `except` addition in the Groq tier of model.py.

---

### Video Forge — forge.py (Root Level)

Working proof-of-concept built and tested. MoviePy 2.x only — 1.x syntax is incompatible.

**Key API changes (1.x → 2.x):**
| 1.x (broken) | 2.x (correct) |
|---|---|
| `from moviepy.editor import ...` | `from moviepy import ...` |
| `.subclip(0, n)` | `.subclipped(0, n)` |
| `.crop(x1=, y1=, x2=, y2=)` | `.cropped(x1=, y1=, x2=, y2=)` |
| `.resize(height=, width=)` | `.resized(new_size=(w, h))` |
| `.set_audio(track)` | `.with_audio(track)` |
| `.set_duration(n)` | `.with_duration(n)` |
| `.set_position(...)` | `.with_position(...)` |

**Captions = ImageMagick build-trap.** `TextClip` on Windows requires ImageMagick installed + path-configured. Skip for any proof/free sample. Add only post-payment using Pillow text layer (MoviePy 2.x native, no ImageMagick).

**Render settings (8GB-safe):**
```python
clip.write_videofile(out, fps=24, threads=1, preset="ultrafast",
                     codec="libx264", audio_codec="aac", logger="bar")
```

**Current limitation:** takes one video clip for entire audio track. No per-scene B-roll matching. That's `video_forge.py` (next sanctioned media build, revenue-critical only).

---

### Freelance Track — Current State (as of 2026-08-23)

**Status:** Winding down. No active clients. Discontinuing unless a client closes within days.

**Gate closed (Ok_Abroad_3627 thread):**
- Roman Empire proof render completed (`roman_pilot.mp4`)
- Correct pitch sent (plain English, no jargon, free proof + $150 batch offer)
- No confirmed deposit received
- Thread inactive

**Pricing locked (do not deviate):**
- 30 Shorts batch: $150–200 (service delivery, NOT source code)
- NEO system deployment: $500–2k setup + $200–500/mo retainer (client's own keys, IP protected)
- Source code flat-fee sales: BLOCKED — permanently sub-floors the IP value

**Freelance Gem — v3.0 knowledge file produced this session.**
Key additions vs v2: capability gate (CAN/CANNOT lists), anti-fabrication lock, NEO deployment tier, buyer-temperature read, plain-English client copy rule, DDG dead + googlesearch blocked corrections.

**Hard stops (permanent):**
- No SMTP cold mail (personal or burner)
- No LinkedIn/FB automation
- No creator-profile quotes (handles, followers, niches)
- No fabricated samples or portfolio data
- No CapEx fronted before confirmed deposit
- Free-tier ceiling: ~250 SerpApi searches/mo (~100 clean leads)

---

### NEO — Operational Mode Change

**notch.py + voice.py: ABANDONED as daily tools.** Not good enough for daily use yet. Both remain in the public repo as portfolio proof of range (ctypes AppBar + offline STT are technically impressive). Do not rebuild or polish — sequenced post income-floor.

**What stays active (revenue-critical only):**
- `data_janitor.py` — Node 2 profit center, interview demo asset
- `reddit_bounty_tracker.py` — live job monitor
- B2B pipeline (`b2b_hr_scraper` → `b2b_enrich` → `b2b_sanitize`)
- `image_prompt_batcher.py` — media pipeline node 1
- `forge.py` — proof render, doubles as interview demo clip source

---

*Last updated: 2026-08-23*
