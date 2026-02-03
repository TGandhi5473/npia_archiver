import streamlit as st
import pandas as pd
import numpy as np
from core.scraper import NovelArchiver

st.set_page_config(page_title="NPIA Encyclopedia", layout="wide", page_icon="📚")

if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Settings")
    exclude_19 = st.checkbox("Hide 18+ 🔞")
    only_plus = st.checkbox("Only Plus 💎")
    if st.button("🔄 Reload DB"):
        st.cache_data.clear()
        st.rerun()

df = st.session_state.archiver.db.get_all_novels_df()
if not df.empty:
    if exclude_19: df = df[df['is_19'] == 0]
    if only_plus: df = df[df['is_plus'] == 1]

tab_scrape, tab_encyclo, tab_tags = st.tabs(["🚀 Scraper", "🔍 Encyclopedia", "🏷️ Tag Manager"])

# --- TAB 1: SCRAPER ---
with tab_scrape:
    st.header("Scraper Control")
    start_id = st.number_input("Start ID", value=400000)
    stop_id = st.number_input("Stop ID", value=400005)

    if st.button("▶️ Start Scraper"):
        ids = [str(i) for i in range(int(start_id), int(stop_id) + 1)]
        progress_bar = st.progress(0)
        log_container = st.empty()
        
        # Error Blacklist for common noisy messages
        blacklist = ["NoneType", "attribute", "Cloudflare", "ReadTimeout"]
        recent_logs = []

        for idx, nid in enumerate(ids):
            res = st.session_state.archiver.scrape_novel(int(nid))
            
            # Logic to clean up log messages
            if res == "Saved": msg = f"✅ ID {nid}: Saved"
            elif res == "Cached": msg = f"📂 ID {nid}: Cached"
            elif res == "Filtered": msg = f"⏭️ ID {nid}: Low Quality"
            elif "Parse Error" in res: msg = f"🗑️ ID {nid}: Removed/Private"
            elif any(e in res for e in blacklist): msg = f"⚠️ ID {nid}: System Busy"
            else: msg = f"❌ ID {nid}: {res[:30]}"

            recent_logs.insert(0, msg)
            if len(recent_logs) > 5: recent_logs.pop()
            
            log_container.code("\n".join(recent_logs))
            progress_bar.progress((idx + 1) / len(ids))
        
        st.success("Finished!")
        st.rerun()

# --- TAB 2: ENCYCLOPEDIA ---
with tab_encyclo:
    if not df.empty:
        avg_chaps = df['chapters'].mean()
        st.metric("Avg Chapters", int(avg_chaps) if pd.notnull(avg_chaps) else 0)
        st.dataframe(df, use_container_width=True, hide_index=True)

# --- TAB 3: TAGS ---
with tab_tags:
    if not df.empty:
        all_tags = [t for s in df['tags_en'] if isinstance(s, list) for t in s]
        if all_tags:
            counts = pd.Series(all_tags).value_counts().reset_index()
            counts.columns = ['Tag', 'Count']
            # Safe max for ProgressColumn
            m_val = counts['Count'].max()
            s_max = int(m_val) if pd.notnull(m_val) and m_val > 0 else 1
            st.dataframe(counts, column_config={"Count": st.column_config.ProgressColumn(max_value=s_max)}, use_container_width=True)
