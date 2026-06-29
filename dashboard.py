"""
dashboard.py — NEO Command Center (Streamlit)
============================================
Run: streamlit run dashboard.py

Panels:
- Live system status (state.txt) + RAM/CPU
- Active task with Done/Dismiss/Skip (notch_state.json — mirrors the Notch HUD)
- Quick-action shortcuts (preset directives -> NeoBrain)
- Bounty feed (bounty_log.csv)
- Directive chat (ReAct)

RAM: 8GB-safe. No auto-polling — manual Refresh button (respects the no-always-on rule).
psutil optional (metrics hidden if absent).
"""

import os
import csv
import json
import time
from pathlib import Path
from datetime import datetime

import streamlit as st

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pandas as pd
except ImportError:
    pd = None

from neo.brain import NeoBrain

# ── Paths ─────────────────────────────────────────────────────────────────────

ROOT        = Path(__file__).parent
STATE_FILE  = ROOT / "state.txt"
NOTCH_STATE = ROOT / "notch_state.json"
BOUNTY_LOG  = ROOT / "bounty_log.csv"

# ── Page config ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="NEO Command Center", layout="wide", page_icon="🔥")

# ── Session init ────────────────────────────────────────────────────────────────

if "brain" not in st.session_state:
    st.session_state.brain = NeoBrain()
if "history" not in st.session_state:
    st.session_state.history = []

# ── Helpers ───────────────────────────────────────────────────────────────────

def read_state() -> str:
    try:
        return STATE_FILE.read_text(encoding="utf-8").strip() or "IDLE"
    except Exception:
        return "IDLE"

def state_badge(s: str):
    low = s.lower()
    if "listen" in low or "green" in low:
        return "#00FF00", "LISTENING"
    if "process" in low or "blue" in low:
        return "#00BFFF", "PROCESSING"
    return "#888888", "IDLE"

def read_task() -> dict:
    try:
        return json.loads(NOTCH_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def write_task_status(status: str):
    data = read_task()
    data["status"] = status
    try:
        NOTCH_STATE.write_text(json.dumps(data), encoding="utf-8")
    except Exception:
        pass

def read_bounties(n: int = 20):
    if not BOUNTY_LOG.exists():
        return []
    try:
        with open(BOUNTY_LOG, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        return rows[-n:][::-1]
    except Exception:
        return []

def run_directive(text: str):
    st.session_state.history.append({"role": "user", "content": text})
    with st.spinner("Processing directive autonomously..."):
        try:
            summary = st.session_state.brain.run(text)
        except Exception as e:
            summary = f"⚠️ Error: {e}"
    st.session_state.history.append({"role": "assistant", "content": summary})

# ── Sidebar: status, metrics, task, shortcuts ──────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ SYSTEM")
    color, label = state_badge(read_state())
    st.markdown(
        f"<div style='font-size:20px;color:{color};font-weight:bold'>● {label}</div>",
        unsafe_allow_html=True,
    )
    if psutil:
        c1, c2 = st.columns(2)
        c1.metric("RAM", f"{psutil.virtual_memory().percent:.0f}%")
        c2.metric("CPU", f"{psutil.cpu_percent(interval=0.1):.0f}%")

    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

    st.divider()

    # Active task
    st.markdown("## 📋 ACTIVE TASK")
    task = read_task()
    task_text = task.get("task") or task.get("suggestion") or "No active task"
    task_status = task.get("status", "PENDING")
    st.info(f"{task_text}\n\n**Status:** {task_status}")
    t1, t2, t3 = st.columns(3)
    if t1.button("✅ Done", use_container_width=True):
        write_task_status("COMPLETED"); st.rerun()
    if t2.button("✗ Dismiss", use_container_width=True):
        write_task_status("DISMISSED"); st.rerun()
    if t3.button("→ Skip", use_container_width=True):
        write_task_status("SKIPPED"); st.rerun()

    st.divider()

    # Quick-action shortcuts
    st.markdown("## 🎯 SHORTCUTS")
    SHORTCUTS = {
        "🔍 Summarize latest bounties": "Read bounty_log.csv and summarize the most recent high-value freelance leads.",
        "🧹 Clean a CSV": "Run the data_janitor workflow: ask me for a CSV path, then profile and auto-clean it.",
        "🕷️ Scrape a site": "Ask me for a target URL and the fields to extract, then run the zero-noise scraper.",
        "📊 System health check": "Report current system status, running background scripts, and any errors in the session log.",
    }
    for label_btn, directive in SHORTCUTS.items():
        if st.button(label_btn, use_container_width=True):
            run_directive(directive)
            st.rerun()

# ── Header ──────────────────────────────────────────────────────────────────────

st.markdown(
    "<h1 style='text-align:center;color:#00FFFF;margin-bottom:0'>A.V.E.N.G.E.R.S. COMMAND CENTER</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align:center;color:#888'>Neural Environment Operations (N.E.O.)</p>",
    unsafe_allow_html=True,
)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_chat, tab_bounty = st.tabs(["💬 Directive", "🎯 Bounty Feed"])

with tab_chat:
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    task_in = st.chat_input("Sir, what is your directive?")
    if task_in:
        with st.chat_message("user"):
            st.markdown(task_in)
        run_directive(task_in)
        st.rerun()

with tab_bounty:
    st.markdown("#### Recent freelance bounty hits")
    bounties = read_bounties(20)
    if not bounties:
        st.caption("No hits logged yet. Start `reddit_bounty_tracker.py` to populate `bounty_log.csv`.")
    elif pd is not None:
        df = pd.DataFrame(bounties)
        cols = [c for c in ["timestamp", "subreddit", "matched_keyword", "title", "url"] if c in df.columns]
        st.dataframe(df[cols], use_container_width=True, hide_index=True,
                     column_config={"url": st.column_config.LinkColumn("url")} if hasattr(st, "column_config") else None)
    else:
        for b in bounties:
            st.markdown(f"**{b.get('subreddit','?')}** · `{b.get('matched_keyword','')}` — "
                        f"[{b.get('title','')[:80]}]({b.get('url','')})")
