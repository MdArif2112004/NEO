# N.E.O. — CLAUDE.md

> **Context document for Claude / Cline. Human-only edits. Do not modify via agent.**

---

## What NEO Is

Local Python AI terminal. ReAct loop (Think → Act → Observe). 8GB RAM / Windows. i3 / 2 cores.

**Failover chain:** Gemini 2.0 Flash → Groq (`openai/gpt-oss-120b`) → Ollama (local Llama 3.2)

**Entry points:**
- `run_neo.py` — direct terminal (A.V.E.N.G.E.R.S. Interface)
- `start_neo.sh` — background boot (Linux) for the alerting matrix

---

## Binding Constraints

- **8GB RAM / 2 cores** — trigger-based only. No always-on polling. No memory-bloat frameworks.
- **Banned:** Docker, LangChain, CrewAI, AutoGen, ChromaDB. Pure Python only.
- **Cowork unavailable** (Win 11 Home, no Hyper-V / vmms). Use Claude Code + Cline instead.
- **Token budget** shared across chat + Claude Code. Build off-peak (IST mornings/afternoons).
- **Solo operator** — ship working modules, no gold-plating.

---

## Entry Points & Boot Sequence

| File | Description |
|------|-------------|
| `run_neo.py` | Command-line entry — A.V.E.N.G.E.R.S. Terminal Interface for direct interactions. |
| `start_neo.sh` | **Master Boot Sequence (Linux)** — Background ignition: 5s stability delay, then `nohup python3` launches `reddit_bounty_tracker.py`, `telegram_router.py`, `voice.py`, `notification_server.py` (logs to `logs/`). Runs from the repo root and self-chmods. Replaces the old `start_neo.bat`. |
| `requirements.txt` | Python dependencies |
| `README.md` | Project overview |
| `NEO_MASTER_CODEX.md` | Full architecture codex (for Gemini Architect Gem — not Claude). |
| `cmd_media_codex.md` | CMD Gem operating reference — Revenue track, outreach protocol, platform safety rules. |

---

## Core Agent Files (Root Level)

| File | Description |
|------|-------------|
| `observer.py` | Background observer / watcher |
| `telegram_router.py` | Encrypted Telegram alerting + remote commands |
| `voice.py` | **Voice Interface (Vosk offline STT + command grammar + system TTS).** Grammar-locked: only the fixed phrases in `ACTIONS` are recognized, so commands can't be misheard ("open youtube" can't become "open you to"). Loads model from `models/vosk-en/`. Free-vocab window only inside `ask neo` / `search youtube`. Updates `state.txt`. Speaks via `neo_voice.speak`. Clap-to-wake dropped. Deps: vosk, sounddevice, pyttsx3. |
| `voice_test.py` | Voice test script |
| `mic_test.py` | Microphone test script |
| `dashboard.py` | Streamlit local web UI for monitoring |
| `notification_server.py` | **Local Notification Server** — Lightweight HTTP server on `127.0.0.1:51820` + `notify-py` (libnotify/DBus) for desktop alerts. Started by `start_neo.sh`. Accepts `{title, message, duration}` — `duration` is ignored, the desktop owns toast expiry. |
| `state.txt` | State tracker written by `voice.py` / `neo_ears.py` and surfaced by `dashboard.py` (Gray=Idle, Green=Listening, Blue=Processing) |
| `command_center.html` | HTML command center UI |

### Audio / Video Assets (Root)

| File | Description |
|------|-------------|
| `alert.wav` | Alert sound |
| `success.wav` | Success sound |
| `gameplay.mp4` | Gameplay video |

### Leads & Data Files (Root)

| File | Description |
|------|-------------|
| `raw_leads.csv` | Raw lead data |
| `test_leads.csv` | Test lead data |
| `bounty_leads.txt` | Bounty program leads |
| `messy_leads.txt` | Unprocessed lead list |
| `targets.csv` | Target list |
| `ohio_venues.csv` | Ohio venue scraping results |
| `trending.json` | Trending topics data |
| `bounty_log.csv` | **Bounty tracker hit log** — auto-appended by `reddit_bounty_tracker.py`. Columns: timestamp, stream, subreddit, title, url, matched_keyword. |
| `B2B_HR_Raw.csv` | **B2B collector output** — raw company names + locations from directory scraper |
| `B2B_HR_Leads_Enriched.csv` | **B2B enricher output** — websites + emails resolved via SerpApi |
| `B2B_HR_Leads_PoC.csv` | **B2B PoC deliverable** — sanitized top-N rows, zero blank emails |

### Revenue Track Files (Root)

| File | Description |
|------|-------------|
| `reddit_bounty_tracker.py` | **Reddit Bounty Tracker** — RSS-based live monitor for 14 freelance subreddits. Zero credentials. Persistent `requests.Session` primed with reddit.com cookies + rotating `HEADERS_POOL` (Chrome/Firefox) + random 8–14s per-sub delay — fixes blanket 403s on residential IP. Fires a `notify-py` desktop toast, auto-opens URL, logs to `bounty_log.csv`. Blacklist gates: geo / comp / onsite / role-type (incl. adult-content terms: "female streamer", "cam model", "slim", "appearance"). Stale-post guard (SCRIPT_START). Rate-limit backoff (15-min cooldown). Deps: `requests feedparser notify-py`. Boot: `nohup python3 reddit_bounty_tracker.py` via `start_neo.sh`. |

### Content / Output Files (Root)

| File | Description |
|------|-------------|
| `script.txt` | Generated script |
| `response.txt` | Agent response output |
| `conversation.txt` | Conversation log |
| `email_dump.txt` | Email data dump |
| `voice_log.txt` | Voice interaction log |
| `apex_brief.txt` | Apex competitive brief |
| `youtube_tools.txt` | YouTube tool notes |
| `wardialing_report.txt` | Wardialing scan report — excluded from public repo |

### Downloads

| File | Description |
|------|-------------|
| `downloads/venue_text_pricing.json` | Venue pricing data |
| `downloads/pdfs/` | Downloaded PDFs directory |

---

## `neo/` — Core Agent Package

| File | Description |
|------|-------------|
| `neo/__init__.py` | Package initializer |
| `neo/brain.py` | **⚠️ IMMUTABLE — NEVER MODIFY THE LOOP.** NeoBrain ReAct engine. Think → Act → Observe. Orchestrates all 38 tools. 380 lines. Has `CORE_FILES` protection + `_permitted()` QA gate blocking unsafe subprocess execution. |
| `neo/config.py` | **Failover Matrix (Part 1)** — Hardware-optimized API router config |
| `neo/discord_bot.py` | **Shadow Exchange C&C** — Two-way remote Command & Control. Listens passively via Bot Token for keyword bounties, serves alerts via `notify-py`. |

### `neo/llm/` — LLM Failover Router

| File | Description |
|------|-------------|
| `neo/llm/__init__.py` | Package marker |
| `neo/llm/model.py` | **LLM Failover Router** — Cascades: Gemini 2.0 Flash → Groq `openai/gpt-oss-120b` → Local Ollama. Zero-downtime against 429s. |

### `neo/memory/` — Memory System

| File | Description |
|------|-------------|
| `neo/memory/__init__.py` | Package marker |
| `neo/memory/store.py` | **Session Memory Store** — Short-term JSON step history. Real-time error logging. |

---

## `neo/tools/` — Tool Library

### Quick-Reference by Category

| Category | Tools |
|----------|-------|
| **Comms / Outreach** | `outbound_strike.py` (B2B cold email, Gmail SMTP, human-mimicry throttle), `discord_bot.py` (C&C bridge), `discord_bridge.py`, `discord_api.py`, `discord_spider.py` (bounty keyword listener), `telegram_router.py` |
| **Scraping / OSINT** | `scrape_master.py` (Playwright + BS4, 8GB-safe, drops CSS/media), `scrape_ohio.py`, `trend_scraper.py`, `venue_link_harvest.py`, `blast_venues.py`, `web_researcher.py`, `b2b_hr_scraper.py` |
| **Data / Files** | `universal_ingest.py` (TXT/CSV/PDF → JSON, row-by-row RAM-safe), `filesystem.py`, `pdf_extractor.py`, `bulk_downloader.py`, `clip_ingest.py`, `notion_api.py` (RAG bridge, `push_csv_to_notion`), `notion_pipeline.py`, `check_notion.py`, `discover_notion.py`, `content_validator.py` (scraper validation gate), `data_janitor.py`, `b2b_sanitize.py` |
| **Enrichment** | `b2b_enrich.py` (SerpApi website + email resolver), `web_researcher.py` |
| **Media / Content** | `media_forge.py`, `video_forge.py` (short-form video render), `script_matrix.py`, `content_writer.py`, `tts_engine.py`, `compress_video.py`, `youtube_publisher.py`, `arbitrage.py`, `image_prompt_batcher.py` |
| **AI / Memory** | `deep_memory.py` (local RAG, Ollama + numpy cosine, zero cloud), `error_memory.py`, `meta_coder.py` (auto-generates new tools), `screen.py` (OCR/Vision), `vision_strike.py`, `system_audio.py`, `neo_voice.py` |
| **System / QA** | `testing.py`, `benchmark_node.py`, `permission.py`, `cold_reboot.py` (kills the background processes, flushes the module cache, restarts via `python3 run_neo.py`), `validate_edits.py` (syntax check, missing init, stale .bak detection) |

### Full Tool Index

| File | Description |
|------|-------------|
| `neo/tools/arbitrage.py` | **Arbitrage Pipeline** — Content arbitrage across platforms |
| `neo/tools/b2b_enrich.py` | **Website + Email Enricher v3** — Primary: SerpApi (free 250/mo, real Google results, set `SERPAPI_KEY` in `.env`). Fallback: Bing HTML scrape (zero setup). Resolves company website, scrapes `/contact` for email with junk-filter + priority ranking. Reads `B2B_HR_Raw.csv` → `B2B_HR_Leads_Enriched.csv`. Deps: requests, beautifulsoup4. |
| `neo/tools/b2b_hr_scraper.py` | **B2B Directory Collector** — Paginated Playwright scraper. Collects Company Name + Location across listing pages only (Clutch paywalls website URLs, so no per-profile visits). Cloudflare detection. Output: `B2B_HR_Raw.csv`. Deps: playwright. |
| `neo/tools/b2b_sanitize.py` | **Deliverable Sanitizer** — dropna → blank/dedupe filter → top-N slice. Pandas 3.x-safe (dropna BEFORE string filters). Reads enriched CSV → `B2B_HR_Leads_PoC.csv`. Deps: pandas. Now includes MX-record validation (dnspython) + domain-mismatch flagging + npm/CSS/placeholder junk filters. |
| `neo/tools/benchmark_node.py` | **Benchmarking** — Local execution sandbox. Compares prompt metrics vs. live APIs. Dumps markdown logs to `evaluation_output.md`. |
| `neo/tools/blast_venues.py` | **Venue Blast** — Mass venue outreach |
| `neo/tools/bulk_downloader.py` | **Bulk Downloader** — Mass file download utility |
| `neo/tools/check_notion.py` | **Notion Check** — Verify Notion database connection |
| `neo/tools/clip_ingest.py` | **Clip Ingestion** — Media clip ingestion pipeline |
| `neo/tools/cold_reboot.py` | **Cold Reboot Engine** — Module Cache Phantom fix (Linux). Kills the Neo background processes by name (`pgrep` + `SIGKILL`, never a blanket python kill), flushes the module cache, relaunches `python3 run_neo.py` detached. Run after editing any background script. |
| `neo/tools/compress_video.py` | **Video Compressor** — File size reduction |
| `neo/tools/content_validator.py` | **Zero-Noise Validation Gate** — Pre-save content validator. `validate_pricing_doc(raw_bytes, entity)`: checks magic bytes (`%PDF`), size bounds (3KB–15MB), pricing signal count (≥3), entity relevance (venue name token). `validate_pricing_text(text, entity)`: same logic for scraped HTML. `rank_candidates(links)`: scores links by anchor/URL keyword strength, returns best-first. Prevents blind ingestion. RAM: low (`pypdf` only — never `pdfplumber`). Dep: `pip install pypdf`. |
| `neo/tools/content_writer.py` | **Content Writer** — AI-driven content generation |
| `neo/tools/data_janitor.py` | **Data Janitor (Node 2 — client-ready)** — CSV/XLSX cleaning engine. Profile, 1-click auto-clean (snake_case headers, trim, drop empties, dedupe, Int64 coercion) with client-facing `.md` report via `export_report()` — includes a **Quality Score /100**, before/after delta table, and column-changes section. NL commands (Groq → whitelisted JSON op, NO code exec — matches brain.py QA gate) incl. `title_case`, `standardize_phone`. Batch mode: `batch_clean(folder)` + `export_batch_report()` via `--batch <folder> [--out <dir>]`. Undo, export. Powers the Fiverr data gig. Pandas 3.0-safe: `pd.api.types.is_string_dtype` (not `dtype==object`) + `df.copy()` for Copy-on-Write. Deps: pandas, openpyxl, groq (optional). Groq calls now use openai/gpt-oss-120b with reasoning_effort="low" (reasoning model — keeps JSON clean + caps token burn). |
| `neo/tools/deep_memory.py` | **Zero-Cost Local RAG** — Ollama (`nomic-embed-text`) + numpy cosine similarity. 100% cloud-independent, rate-limit immune. |
| `neo/tools/discord_api.py` | **Discord API** — Low-level Discord API integration |
| `neo/tools/discord_bridge.py` | **Discord Bridge** — Message relay between Neo and Discord |
| `neo/tools/discord_spider.py` | **Discord Spider** — Scrapes channels/guilds for keyword bounties. Paired with `discord_bot.py` for Shadow Exchange C&C. |
| `neo/tools/discover_notion.py` | **Notion Discover** — Dynamic Notion database discovery and querying |
| `neo/tools/error_memory.py` | **Error Memory** — Log and recall past errors for debugging |
| `neo/tools/filesystem.py` | **Filesystem Ops** — Read/write/manage local files |
| `neo/tools/image_prompt_batcher.py` | **Media Pipeline #1** — Script .txt → numbered Ideogram image prompts, each prefixed with locked art-style prefix (`media/character_ref/style_prefix.txt`). Groq-generated, JSON-array parsed. Output: `media/assets/<video_id>/prompts.txt` (paste-ready) + `prompts_numbered.txt`. Deps: groq. Groq calls now use openai/gpt-oss-120b with reasoning_effort="low" (reasoning model — keeps JSON clean + caps token burn). |
| `neo/tools/media_forge.py` | **Media Forge** — Media creation and manipulation |
| `neo/tools/meta_coder.py` | **Meta-Coder** — Autonomously generates new tools and capabilities |
| `neo/tools/neo_voice.py` | **Voice Synthesis** — `speak()` via pyttsx3 (configured system SAPI voice), PowerShell SAPI fallback if pyttsx3 missing. Called by `voice.py`. Piper was evaluated and rejected (poor quality on 8GB medium voices; uninstalled). |
| `neo/tools/notion_api.py` | **Notion RAG Bridge** — Connects ARIF_OS and NEO CONTROL. `push_csv_to_notion`: reads arbitrary CSV headers, builds matching Notion columns dynamically without templates. |
| `neo/tools/notion_pipeline.py` | **Notion Pipeline** — Automated Notion data pipeline |
| `neo/tools/outbound_strike.py` | **Cold Outbound Engine** — Reads `targets.csv`, authenticates via Gmail SMTP, executes B2B pitches with randomized human-mimicry throttling. 8GB RAM-optimized (iterative). ⚠️ See Revenue Track Guardrails before use. |
| `neo/tools/pdf_extractor.py` | **PDF Extractor** — Extract text from PDFs |
| `neo/tools/permission.py` | **Permission Manager** — Tool execution safety controls |
| `neo/tools/scrape_master.py` | **Headless OSINT Scraper** — Playwright + BeautifulSoup. Intercepts/drops CSS, image, media payloads. 8GB RAM-safe. Must implement Zero-Noise Scraper Protocol on every build. |
| `neo/tools/scrape_ohio.py` | **Ohio Venue Scraper** — Specialized Ohio venue scraper |
| `neo/tools/screen.py` | **OCR / Vision Matrix** — Screen capture + OCR, tied to Notch HUD. `capture_chatgpt()` deprecated — API endpoints only. |
| `neo/tools/script_matrix.py` | **Script Matrix** — Content script generation for video/audio pipelines |
| `neo/tools/system_audio.py` | **System Audio** — Audio capture, playback, and routing |
| `neo/tools/testing.py` | **Auto-Testing** — Automated test execution for validating capabilities |
| `neo/tools/trend_scraper.py` | **Trend Scraper** — Social/web trend scraping for content direction |
| `neo/tools/tts_engine.py` | **TTS Engine** — Text-to-speech voiceover generation |
| `neo/tools/universal_ingest.py` | **Data Ingestion Engine** — Low-RAM parser for TXT/CSV/PDF → JSON. Row-by-row streaming via Groq to prevent memory overflow. |
| `neo/tools/validate_edits.py` | **3-Command Validation Pass** — Scans all Python: syntax errors (`ast.parse`), missing `__init__.py`, stale `.bak` files, versioned duplicates (`v1_`, `v2_`). |
| `neo/tools/venue_link_harvest.py` | **Venue Link Harvester** — Harvests venue contact links from web |
| `neo/tools/video_forge.py` | **Video Forge** — Short-form video render (shorts) |
| `neo/tools/vision_strike.py` | **Vision Strike** — Vision-based screen analysis and content extraction |
| `neo/tools/web_researcher.py` | **Web Researcher** — Web research and structured report generation |
| `neo/tools/youtube_publisher.py` | **YouTube Publisher** — Auto-uploads rendered content to YouTube |

---

## Zero-Noise Scraper Protocol

**Mandatory for every Playwright / BeautifulSoup scraper build. Do not write scraper code until these rules are applied.**

### Rule 1 — Pre-Flight Gatekeeper (URL + Anchor Filter)
- Never download a file or scrape a sub-page blindly.
- Inspect `href` URL + anchor text FIRST against a WHITELIST (e.g. "pricing", "rates") and BLACKLIST (e.g. "menu", "investor", "terms").
- **Blacklist wins** over whitelist. Check blacklist first.
- Use **case-insensitive word-boundary** matching — not bare substring (avoids "menu" hitting "venue").
- If no whitelist match or blacklist hit: SKIP.

### Rule 2 — Resource Starvation (8GB RAM)
- Block images, fonts, CSS, media via `route.abort()`.
- **Never block `script` or `document`** — pricing is often JS-rendered.

### Rule 3 — Candidate Ranking (Best-First, Not First-Found)
- When multiple links pass the whitelist, score them: exact "pricing" anchor > "rates" > contains keyword; on-domain > off-domain; `.pdf` gets +1.
- Use `content_validator.rank_candidates(links)` — try highest score first.
- Accept only after Rule 4 passes. Fall through to next candidate on failure.

### Rule 4 — Artifact Validation (Post-Download, Pre-Save) ← the job-saving rule
- Import and call `content_validator.validate_pricing_doc()` or `validate_pricing_text()` BEFORE writing any file.
- For PDFs: verify magic bytes (`%PDF`), size bounds (3KB–15MB), ≥3 pricing signals, entity name token present.
- For HTML page text: same pricing signal + entity checks.
- If validation returns `False` → discard, never save.

### Rule 5 — Batch Export (RAM Safety)
- Use `csv.writer` with a single header written once. Append per-row or every 50 rows.
- Never hold full result arrays in memory. Never use pandas `.to_csv(mode='a')` in loops (duplicate header risk).

---

## B2B Lead Pipeline (Over-Extract & Filter)

3-step pipeline. Never send a client partial/blank data — over-extract, enrich, filter to exactly N pristine rows.

| Step | Command | Output |
|------|---------|--------|
| 1. Collect | `python neo/tools/b2b_hr_scraper.py <url> 150` | `B2B_HR_Raw.csv` (150 names+locations) |
| 2. Enrich | `python neo/tools/b2b_enrich.py` | `B2B_HR_Leads_Enriched.csv` (website + email via SerpApi) |
| 3. Sanitize | `python neo/tools/b2b_sanitize.py 50` | `B2B_HR_Leads_PoC.csv` (50 perfect rows, 0 blank emails) |

**Why over-extract:** email yield is ~30-50% — scrape ~3× the target so the filtered result still hits N.

**Directory paywall rule:** Clutch (and most B2B directories) hide website URLs for logged-out users. Do NOT scrape websites from the listing — resolve them via SerpApi enrichment in step 2.

**If sanitize reports "short of N":** raise MAX_RESULTS in the scraper and re-run.

### The 4 reusable templates this maps to

| Template | Built as |
|----------|----------|
| Base Playwright Scraper | `b2b_hr_scraper.py`, `scrape_master.py` |
| X-Ray Searcher (SerpApi primary / Bing fallback — NOT googlesearch) | `b2b_enrich.py` |
| Data Sanitizer | `data_janitor.py`, `b2b_sanitize.py` |
| SMTP Sender | `outbound_strike.py` ⚠️ Gmail cold = account burn (see Guardrails) |

---

## NEO Capability Boundaries (Zero-CapEx Reality)

NEO is a single-thread script runner on an 8GB residential IP — not a server farm. Know the boundary before building.

### ✅ Where NEO dominates (zero CapEx)

- **Data cleaning / formatting (Node 2 — peak)** — pandas + regex, offline, zero ban risk, instant. 50k-row messy CSV → clean in seconds. This is the profit center.
- **Dumb/static HTML scraping** — local directories, yellow pages, unshielded registries, basic WordPress sites.
- **API-to-API routing** — Make.com / Notion / Telegram. Zero compute, zero ban risk.
- **Low-volume meta-dorking** — DDG snippet extraction for specific emails. Sniper tool, NOT a bulk engine.

### ❌ Where NEO fails without CapEx (do NOT attempt at scale)

- **Tier-1 social at scale (Instagram / Facebook / LinkedIn)** — residential IP blacklisted in ~20 min. Needs rotating residential proxies (~$50/mo).
- **Cloudflare Turnstile / Datadome sites (Clutch website-unlock, YC, Apollo)** — cannot bypass free.
- **Multi-thread Playwright on 8GB** — crashes the rig. Single-thread synchronous loops only.
- **Bulk search-engine dorking** — DDG rate-limits a residential IP as fast as Tier-1 social. Scope deliverables to low thousands, never 100k.

**CapEx lock:** No rotating proxies, VPS, or paid OSINT APIs until the ₹14,000 baseline is secured from Node 2 + static scraping. Infrastructure is funded by revenue, never out-of-pocket.

---

## Directory Map (Non-Core)

| Directory | Contents |
|-----------|----------|
| `renders/` | `compressed_test.mp4`, `script_1_Voxel_Space.mp4`, `script_2_Anthropic_surpasses_.mp4` |
| `audio/` | `script_1_Voxel_Space.mp3`, `script_2_Anthropic_surpasses_.mp3` |
| `scripts/` | `script_1_Voxel_Space.txt`, `script_2_Anthropic_surpasses_.txt`, `script_3_Openrsync` |
| `experiments/` | `fetch_btc_price.py`, `btc_price.txt` |
| `solo_leveling/` | `app.py`, `data.json` (Solo Leveling themed sub-app) |

---

## Hardening & Security

### Permanent Hardening Applied

| # | Failure Mode | Fix Applied |
|---|-------------|-------------|
| 1 | **ReAct Loop Erasure** | ✅ `brain.py` `CORE_FILES` protection + blocking in run loop — IMMUTABLE |
| 2 | **System OOM (CrewAI/LangChain)** | ✅ Zero heavy frameworks in requirements |
| 3 | **Discord Account Ban** | ✅ Bot Tokens only — no self-bot user tokens |
| 4 | **Module Cache Phantoms** | ✅ `cold_reboot.py` + COLD REBOOT PROTOCOL in SYSTEM_PROMPT |
| 5 | **Subprocess Execution Risk** | ✅ QA Gate in `brain.py._permitted()` — scans `import os`/`import sys` before allowing `run_file()` |
| 6 | **Broken Import Traps** | ✅ All missing `__init__.py` files created across every package directory |
| 7 | **Version Chasing Bloat** | ✅ `validate_edits.py` detects versioned duplicates + 3-Command Validation Pass rule |
| 8 | **UI Scraping Collapses** | ✅ `capture_chatgpt()` deprecated in `screen.py` — redirected to API endpoints |
| 9 | **Blind Scraper Ingestion** | ✅ `content_validator.py` gate — validate magic bytes + pricing signals + entity relevance before any file write. A job was lost to this failure mode. |
| 10 | **Gmail SMTP Account Burn** | ✅ Hard stop — cold email from personal Gmail risks full Google account suspension. Use demand-first Reddit replies instead. `outbound_strike.py` retained but flagged. |
| 11 | **LinkedIn/FB Automation Ban** | ✅ Hard stop — never automate real logged-in LinkedIn or Facebook sessions. LI is a career asset for the CoS pivot. Manual comment pitches only. |
| 12 | **Reddit API Blackout** | ✅ Reddit killed free API key issuance Dec 2025. PRAW abandoned. Bounty tracker uses RSS feeds only (`/r/{sub}/new/.rss`). Rate-limit: IP-based, 15-20 min windows, self-heals. www + old.reddit share the same limit — never retry the fallback on 403/429. |
| 13 | **Pandas 3.x blank-row leak** | ✅ `dropna(subset=[col])` before string filters in all sanitizers — `NaN != ""` is True on pandas 3.x |
| 14 | **Over-scoped social/dork builds** | ✅ NEO Capability Boundaries documented — no Tier-1 social or bulk dorking at zero CapEx; data cleaning + static scraping only |
| 15 | **Groq model decommission** | ✅ Migrated to gpt-oss-120b/20b repo-wide. ⚠️ Failover still 429-only — add model_decommissioned (400) handling to fully harden. |

### `__init__.py` Package Markers Created

- `neo/tools/__init__.py`
- `neo/llm/__init__.py`
- `neo/memory/__init__.py`

---

## Key Learnings (Field-Tested)

- **DDG html endpoint is DEAD for this IP** — hard-blocks residential at any volume. SerpApi (250/mo free) is the enrichment path; Bing scrape is emergency fallback only.
- **Pandas 3.x NaN gotcha:** `NaN != ""` evaluates True, so string-only filters leak blank rows. ALWAYS `df.dropna(subset=[col])` BEFORE any string comparison. (Caught a blank-leak bug in `b2b_sanitize.py` pre-delivery.)
- **Meta-dorking is low-volume:** DDG snippet email extraction is a sniper tool. Search engines throttle a residential IP fast — 100k targets is not feasible at zero CapEx. Scope to low thousands.
- **Voice — grammar beats open-vocab:** a fixed Vosk command grammar eliminates mishears for a known command set. Open-vocab STT (Whisper/Google) garbles short commands. Free-vocab is scoped to `ask neo` / `search youtube` only.
- **Piper TTS rejected:** medium voices sound poor on the 8GB rig; kept the configured Windows SAPI voice. Do not re-attempt Piper.
- **pandas 3.0 traps:** `dtype == object` is always False (StringDtype) — use `pd.api.types.is_string_dtype`; Copy-on-Write silently discards in-place column writes — assign to `df.copy()`.
- **PoC delivery rule:** Over-extract and filter. Scrape ~3× target → enrich → drop blanks → deliver exactly N pristine rows. Never ship partial/blank data; the PoC is the one shot to beat the client's manual VA.
- **Groq free-tier deprecation cycle (~30-day notice):** migrated off llama-3.3-70b-versatile (decommission ~Jul 17 2026) → openai/gpt-oss-120b; llama-3.1-8b-instant (Aug 16 2026) → openai/gpt-oss-20b in clip_ingest.py. New IDs carry a provider/ prefix. gpt-oss is a reasoning model — set reasoning_effort="low" on JSON/structured calls. ⚠️ Failover catches 429s, not 400 model_decommissioned — a dead model string throws uncaught until swapped.
- **Voice mic — peak=1 = level, not permissions:** Vosk silence (capture peak ≈1) with mic access ON means Realtek input volume at 0, not a Windows privacy block (that returns hard 0 / errors). Fix: Settings → Sound → Input → raise mic volume. Working config: default device idx 1 (Microphone Realtek Audio), SAMPLE_RATE=16000.

---

## Revenue Track Guardrails

**These are permanent operator decisions, not session-specific rules.**

| Channel | Status | Reason |
|---------|--------|--------|
| Reddit RSS bounty tracker | ✅ LIVE | Demand-first, zero creds, real-time |
| Reddit manual replies to [Hiring] posts | ✅ PRIMARY | Fastest 24h close path — use free-PoC hook |
| Fiverr gig (Data > Data Processing > Automations) | ✅ LIVE | Passive inbound; expertise: Data extraction, ETL, Manipulation, Normalization, Transformation, Validation, Data flow, Data acquisition |
| Gmail SMTP cold email | ⛔ BLOCKED | Google account suspension risk — not just SMTP, the whole account |
| LinkedIn automation (user_data_dir) | ⛔ BLOCKED | Career asset — permanent LI ban from automation |
| Facebook automation (user_data_dir) | ⛔ BLOCKED | Real account ban risk |
| Discord freelance scraper | ✅ EXISTS | `discord_spider.py` — Bot Token only, safe |
| Clutch.co / Google-dork scraping | ⚠️ DEFERRED | Cloudflare + Google anti-bot walls; do on-demand only, not as primary pipeline |

**Human-in-the-loop rule:** NEO finds targets. Arif approves. NEO sends. Never bypass the manual review step.

---

## Security & Secrets (.clineignore)

The following files are locked and must **never** enter agent context:

- `.env` — environment variables / secrets
- `.clineignore` — Cline ignore rules
- `client_secrets.json` — OAuth client secrets
- `notion_registry.json` — Notion registry credentials
- `*.key` / `*.pem` — any private keys

---

## Environment Variables Required

Names only — values stay in Windows env exclusively (not `.env` file).

`GROQ_API_KEY` · `GEMINI_API_KEY` · `NOTION_API_KEY` · `NEO_TELEGRAM_TOKEN` · `DISCORD_BOT_TOKEN` · `DISCORD_WH_SYSTEM` · `DISCORD_WH_FACTORY` · `DISCORD_WH_OPERATOR` · `DISCORD_WH_CONVERTER`

---

## Known Name Mismatches (Architecture Doc vs. Disk)

| Architecture Doc Name | Actual File On Disk | Status |
|---|---|---|
| `outbound_forge.py` | `neo/tools/outbound_strike.py` | Name mismatch — same function (cold email B2B engine) |
| `startup_scraper.py` | `neo/tools/scrape_master.py` | Name mismatch — same function (8GB Playwright+BS4 scraper) |
| `notification_server.py` | ✅ Exists (was missing — now created) | Fixed |
| `neo/memory/store.py` | ✅ Confirmed exists | Correct |
| Reddit JSON API | ❌ Dead since Dec 2025 | New free app creation disabled. Use RSS only. |

---

## Discord Freelance Spider — Configuration

| Parameter | Value |
|-----------|-------|
| `TARGET_KEYWORDS` | `["python", "scraping", "automation", "bot", "data pipeline", "AI agent"]` |
| `TARGET_SERVER_FRAGMENTS` | `["freelance", "programmer"]` — substring match, case-insensitive |
| `TARGET_CHANNEL_FRAGMENTS` | `["hire", "gig", "freelance", "job", "work"]` — substring match, case-insensitive |
| **Notification routing** | POST to `http://127.0.0.1:51820/` → fallback to a direct `notify-py` toast |
| **Logging** | Writes to `bounty_leads.txt`: timestamp, server, channel, user, content preview, jump link |
| **Boot integration** | Run via `execute_spider()`; `start_neo.sh` boots the 4 core background scripts |
| **Env dependency** | Requires `DISCORD_BOT_TOKEN` |

---

## Reddit Bounty Tracker — Configuration

| Parameter | Value |
|-----------|-------|
| **Auth** | None — RSS feeds, zero credentials |
| **Job subs (14)** | `forhire`, `freelance_forhire`, `freelancer_hire`, `ForHireFreelance`, `Freelancers`, `hireforgigs`, `slavelabour`, `DoneDirtCheap`, `FreelanceIndia`, `remotejobsfinders`, `remoteworking`, `UpworkOfficial`, `LookingforJob`, `creatorservices` |
| **Founder subs (4)** | `entrepreneur`, `smallbusiness`, `saas`, `startups` — low signal; set `FOUNDER_SUBS = set()` to mute |
| **Job title tags** | `[hiring]`, `[task]` |
| **Job keywords** | scrape, data entry, lead list, automation, python, web scraping, data pipeline, bot, crawler, lead generation, data extraction, data cleaning, csv, spreadsheet |
| **Founder keywords** | hire a va, virtual assistant, how to find leads, automate crm, data extraction, lead generation, need a developer, looking for freelancer, find leads |
| **Blacklist: geo** | eu only, europe only, latam only, uk only, us only, eu or latam, hybrid/wfo geographic variants, must be based in, must relocate |
| **Blacklist: comp** | commission based/only, success fee, equity only, unpaid, performance linked, rev share only, percentage of every sale, commission every time, referral fee |
| **Blacklist: onsite** | wfo, work from office, on-site, onsite, in-office, in office, must relocate, must be based in |
| **Blacklist: role** | calendar management, administrative support, email coordination, email management; VA/PA posts without technical keywords |
| **Hybrid guard** | drops "hybrid" only if paired with full-time / office / wfo — protects "hybrid cloud" tech posts |
| **Stale-post guard** | `SCRIPT_START = time.time()` — only alerts on posts published after script start |
| **Rate-limit behavior** | 403/429 = IP rate-limit; does NOT retry old.reddit (same limit). 15-min backoff when ≥⅓ subs rate-limited. Self-heals. |
| **Poll interval** | 300s (5 min) |
| **Fetch delay** | random 8–14s per sub (raised from 5s to beat residential-IP 403s) |
| **Log** | `bounty_log.csv` |
| **Boot** | `nohup python3 reddit_bounty_tracker.py >> logs/reddit_bounty_tracker.log 2>&1 &` in `start_neo.sh` |

---

## Media Pipeline Architecture

- `neo_core/media/` — Root media folder. Subfolders: `character_ref/`, `scripts/`, `assets/channel_1/`, `assets/channel_2/`
- `neo/tools/video_forge.py` *(partially built — forge.py at root, tested)*: Script-to-video pipeline. Inputs: script `.txt` + image prompt list. Outputs: TTS audio (edge-tts) + assembled video (MoviePy) to target `assets/` folder.
- `neo/tools/image_prompt_batcher.py` ✅ **BUILT**: Takes a script, generates numbered image prompt list, saves to `assets/[video_id]/prompts.txt` for manual batch paste into Ideogram.
- `neo/tools/cmd_router.py` *(PLANNED)*: Parses `[NEO_MEDIA_BUILD]` tags from CMD Gem output, dispatches to correct media module.
- **Webhook:** `DISCORD_WH_FACTORY` monitors Channel 1 pipeline completions.

---

## Cross-Gem Communication Protocol

**CMD Gem → NEO Architect handoff:**
```
[NEO_BUILD_REQUEST]
FROM: CMD
REQUEST_TYPE: NEW_MODULE | MODIFY | QUERY
MODULE_NAME: <name>
REQUIREMENT: <plain English>
INTEGRATION_POINT: <where it connects>
PRIORITY: REVENUE_CRITICAL | NICE_TO_HAVE
```

**NEO Architect → CMD handoff:**
```
[NEO_STATUS_UPDATE]
CAPABILITY: <what was added>
MODULE: <path>
USAGE: <instructions for CMD>
```

> Arif is the carrier — copy-paste between systems.

---

*Last updated: 2026-06-27*
