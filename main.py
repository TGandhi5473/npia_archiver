import streamlit as st
import pandas as pd
from core.scraper import NovelArchiver

st.set_page_config(page_title="NPIA Encyclopedia", layout="wide")

if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- SIDEBAR FILTERS (RESTORED) ---
with st.sidebar:
    st.title("🛡️ Filters")
    exclude_19 = st.checkbox("Hide R-18 🔞", value=False)
    only_plus = st.checkbox("Plus Only 💎", value=False)
    only_completed = st.checkbox("Completed Only ✅", value=False)
    
    st.divider()
    if st.button("🔄 Reload Data"):
        st.cache_data.clear()
        st.rerun()

# Load Data
df = st.session_state.archiver.db.get_all_novels_df()

# --- APPLY FILTER LOGIC ---
if not df.empty:
    if exclude_19:
        df = df[df['is_19'] == 0]
    if only_plus:
        df = df[df['is_plus'] == 1]
    if only_completed:
        df = df[df['is_completed'] == 1]

tab_scrape, tab_encyclo, tab_tags = st.tabs(["🚀 Scraper", "🔍 Encyclopedia", "🏷️ Tag Manager"])

# --- TAB 1: SCRAPER (WITH ROLLING LOG) ---
with tab_scrape:
    c1, c2 = st.columns(2)
    sid = c1.number_input("Start ID", value=400000)
    eid = c2.number_input("End ID", value=400005)

    if st.button("▶️ Start Scraper", type="primary"):
        log_box = st.empty()
        recent_logs = []
        
        for nid in range(int(sid), int(eid) + 1):
            res = st.session_state.archiver.scrape_novel(nid)
            
            # Map statuses to clean log messages
            if res == "Cached": m = f"📂 ID {nid}: Skip (Already Archived)"
            elif res == "Saved": m = f"✅ ID {nid}: Successfully Saved"
            elif "Parse Error" in res: m = f"🗑️ ID {nid}: Removed/Private"
            else: m = f"⚠️ ID {nid}: {res[:25]}"

            recent_logs.insert(0, m)
            if len(recent_logs) > 5: recent_logs.pop()
            log_box.code("\n".join(recent_logs))
            
        st.success("Batch Scrape Finished!")
        st.rerun()

# --- TAB 2: ENCYCLOPEDIA ---
with tab_encyclo:
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No novels match your current filters.")
