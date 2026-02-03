import streamlit as st
import pandas as pd
import time
from core.scraper import NovelArchiver

st.set_page_config(page_title="NPIA Archive 2026", layout="wide", page_icon="📚")

# Initialize Archiver in Session State
if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- SIDEBAR: COMMAND CENTER ---
with st.sidebar:
    st.title("🛡️ Command Center")
    
    # Feature 1: Connection & Archive Status
    st.subheader("📊 System Status")
    df_raw = st.session_state.archiver.db.get_all_novels_df()
    total_count = len(df_raw) if not df_raw.empty else 0
    st.metric("Total Archived", total_count)
    
    # Feature 2: Global Filters
    st.divider()
    st.subheader("🔍 Filters")
    exclude_19 = st.checkbox("Hide 18+ 🔞", value=False)
    only_plus = st.checkbox("Plus Only 💎", value=False)
    only_completed = st.checkbox("Completed Only ✅", value=False)
    
    # Feature 3: Actions
    st.divider()
    if st.button("🔄 Reload Database", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- MAIN INTERFACE ---
tab_scrape, tab_encyclo, tab_tags = st.tabs(["🚀 Scraper", "🔍 Encyclopedia", "🏷️ Tag Manager"])

# --- TAB 1: SCRAPER & LOGGING ---
with tab_scrape:
    st.header("Novelpia Scraper")
    
    col1, col2 = st.columns(2)
    start_id = col1.number_input("Start ID", value=400000)
    end_id = col2.number_input("End ID", value=400005)

    if st.button("▶️ Start Batch Scrape", type="primary"):
        # Status & Logging Feature
        status_container = st.status("Initializing Scraper...", expanded=True)
        log_box = st.empty()
        progress_bar = st.progress(0)
        
        logs = []
        ids = range(int(start_id), int(end_id) + 1)
        total = len(ids)

        for i, nid in enumerate(ids):
            status_container.update(label=f"Scraping ID {nid} ({i+1}/{total})")
            
            # Execute scraping logic
            result = st.session_state.archiver.scrape_novel(nid)
            
            # Log formatting
            if result == "Saved":
                logs.append(f"✅ {nid}: Success")
            elif result == "Cached":
                logs.append(f"📂 {nid}: Already Archived")
            elif "403" in result:
                logs.append(f"🛑 {nid}: BLOCKED (403)")
                status_container.update(label="Scraper Blocked!", state="error")
                log_box.code("\n".join(logs))
                st.error("Cloudflare detected the bot. Please wait or change IP.")
                break
            else:
                logs.append(f"⚠️ {nid}: {result}")

            # Update live logging view (keep last 10)
            log_box.code("\n".join(logs[-10:]))
            progress_bar.progress((i + 1) / total)
            
        status_container.update(label="Scrape Finished", state="complete", expanded=False)
        st.rerun()

# --- TAB 2: ENCYCLOPEDIA (FILTERED) ---
with tab_encyclo:
    if not df_raw.empty:
        # Apply Sidebar Filters
        df = df_raw.copy()
        if exclude_19: df = df[df['is_19'] == 0]
        if only_plus: df = df[df['is_plus'] == 1]
        if only_completed: df = df[df['is_completed'] == 1]
        
        st.subheader(f"Showing {len(df)} Results")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("Archive is empty. Start scraping to see data!")
