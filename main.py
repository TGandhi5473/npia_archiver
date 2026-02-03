import streamlit as st
import pandas as pd
import numpy as np
from core.scraper import NovelArchiver

st.set_page_config(page_title="NPIA Encyclopedia 2026", layout="wide")

if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    if st.button("🔄 Clear App Cache"):
        st.cache_data.clear()
        st.rerun()

df = st.session_state.archiver.db.get_all_novels_df()
tab_scrape, tab_encyclo, tab_tags = st.tabs(["🚀 Scraper", "🔍 Encyclopedia", "🏷️ Tag Manager"])

# --- TAB 1: SCRAPER ---
with tab_scrape:
    c1, c2 = st.columns(2)
    sid = c1.number_input("Start ID", value=400000)
    eid = c2.number_input("End ID", value=400005)

    if st.button("▶️ Start"):
        log_box = st.empty()
        blacklist = ["NoneType", "attribute", "Cloudflare"]
        logs = []
        for nid in range(int(sid), int(eid) + 1):
            res = st.session_state.archiver.scrape_novel(nid)
            
            if res == "Saved": m = f"✅ {nid}: Saved"
            elif "Parse Error" in res: m = f"🗑️ {nid}: Removed"
            elif any(e in res for e in blacklist): m = f"⚠️ {nid}: System Busy"
            else: m = f"❌ {nid}: {res[:20]}"
            
            logs.insert(0, m)
            log_box.code("\n".join(logs[:5]))
        st.success("Done!")
        st.rerun()

# --- TAB 2: ENCYCLOPEDIA ---
with tab_encyclo:
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data yet.")

# --- TAB 3: TAG MANAGER ---
with tab_tags:
    st.header("Tag Translation Dictionary")
    
    # Load the live map from the archiver
    current_map = st.session_state.archiver.tag_map
    
    if current_map:
        map_df = pd.DataFrame(list(current_map.items()), columns=['Korean', 'English Translation'])
        
        col_search, col_stats = st.columns([2, 1])
        t_search = col_search.text_input("Search Dictionary...")
        if t_search:
            map_df = map_df[map_df['Korean'].str.contains(t_search) | map_df['English Translation'].str.contains(t_search, case=False)]
            
        col_stats.metric("Total Unique Tags", len(current_map))
        
        st.dataframe(map_df, use_container_width=True, hide_index=True)
        
        # Distribution Chart
        if not df.empty:
            st.subheader("Top Global Tags")
            all_en = [t for s in df['tags_en'] if isinstance(s, list) for t in s]
            if all_en:
                tag_counts = pd.Series(all_en).value_counts().head(20)
                st.bar_chart(tag_counts)
    else:
        st.info("The dictionary is empty. Start scraping to populate it!")
