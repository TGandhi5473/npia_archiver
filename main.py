import sys
import asyncio

# This must happen BEFORE any other imports to fix the Windows subprocess issue
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import streamlit as st
import pandas as pd
from core.scraper import NovelArchiver

st.set_page_config(page_title="NPIA Archive", layout="wide")

if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- SIDEBAR: STATUS & FILTERS ---
with st.sidebar:
    st.header("📊 System Status")
    # Connection Check: Can we see the DB?
    df_raw = st.session_state.archiver.db.get_all_novels_df()
    st.success("Database Connected")
    st.metric("Total Novels", len(df_raw) if not df_raw.empty else 0)

    st.divider()
    st.header("🔍 Global Filters")
    ex_19 = st.checkbox("Hide 18+ 🔞")
    only_p = st.checkbox("Plus Only 💎")
    only_c = st.checkbox("Completed ✅")

# --- MAIN TABS ---
tab_scrape, tab_encyclo = st.tabs(["🚀 Scraper", "🔍 Encyclopedia"])

with tab_scrape:
    c1, c2 = st.columns(2)
    sid = c1.number_input("Start ID", value=400000)
    eid = c2.number_input("End ID", value=400005)

    if st.button("▶️ Start Scrape", type="primary"):
        log_area = st.empty()
        status_bar = st.status("Running Scraper...", expanded=True)
        logs = []

        for nid in range(int(sid), int(eid) + 1):
            status_bar.write(f"Processing ID {nid}...")
            res = st.session_state.archiver.scrape_novel(nid)
            
            logs.append(f"ID {nid}: {res}")
            log_area.code("\n".join(logs[-8:])) # Show last 8 logs
            
            if "403" in res:
                st.error("Cloudflare Block Detected. Stopping Batch.")
                break
        
        status_bar.update(label="Scrape Complete", state="complete")
        st.rerun()

with tab_encyclo:
    if not df_raw.empty:
        # Apply filters
        df = df_raw.copy()
        if ex_19: df = df[df['is_19'] == 0]
        if only_p: df = df[df['is_plus'] == 1]
        if only_c: df = df[df['is_completed'] == 1]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Archive is empty.")
