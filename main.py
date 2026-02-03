import streamlit as st
import pandas as pd
from core.scraper import NovelArchiver

# --- PAGE SETUP ---
st.set_page_config(page_title="NPIA Encyclopedia", layout="wide", page_icon="📚")

# Initialize Archiver in Session State
if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.title("⚙️ Global Settings")
    st.info("Filters applied to Encyclopedia & Tag Manager")
    
    exclude_19 = st.checkbox("Hide 18+ Content 🔞", value=False)
    only_plus = st.checkbox("Only Plus Content 💎", value=False)
    only_completed = st.checkbox("Only Completed ✅", value=False)
    
    st.divider()
    if st.button("🔄 Reload Database", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- LOAD & FILTER DATA ---
df = st.session_state.archiver.db.get_all_novels_df()

if not df.empty:
    # Applying Global Filters
    if exclude_19: df = df[df['is_19'] == 0]
    if only_plus: df = df[df['is_plus'] == 1]
    if only_completed: df = df[df['is_completed'] == 1]

# --- TABS ---
tab_scrape, tab_encyclo, tab_tags = st.tabs(["🚀 Scraper", "🔍 Encyclopedia", "🏷️ Tag Manager"])

# ==========================================
# 1. SCRAPER TAB (Range Logic Restored)
# ==========================================
with tab_scrape:
    st.header("Novelpia Archiver Control")
    
    col_mode, col_info = st.columns([1, 1])
    with col_mode:
        scrape_mode = st.radio("Select Input Method", ["ID Range", "Specific IDs"], horizontal=True)
    
    ids_to_process = []
    
    if scrape_mode == "ID Range":
        c1, c2 = st.columns(2)
        with c1: start_id = st.number_input("Start ID", min_value=1, value=400000)
        with c2: stop_id = st.number_input("Stop ID", min_value=start_id, value=start_id + 5)
        ids_to_process = [str(i) for i in range(int(start_id), int(stop_id) + 1)]
    else:
        manual_ids = st.text_input("Enter IDs (comma separated)", placeholder="401234, 405678")
        ids_to_process = [i.strip() for i in manual_ids.split(",") if i.strip()]

    if st.button("▶️ Start Scraper", type="primary"):
        if not ids_to_process:
            st.warning("Please provide IDs to scrape.")
        else:
            progress_bar = st.progress(0)
            status_area = st.empty()
            log_area = st.container()
            
            for idx, nid in enumerate(ids_to_process):
                status_area.markdown(f"**Current Task:** Scoping ID `{nid}`...")
                res = st.session_state.archiver.scrape_novel(nid)
                
                with log_area:
                    if res == "Saved": st.success(f"ID {nid}: Successfully Archived")
                    elif res == "Cached": st.info(f"ID {nid}: Already in Database")
                    elif res == "Filtered": st.warning(f"ID {nid}: Skipped (Quality Filters)")
                    else: st.error(f"ID {nid}: {res}")
                
                progress_bar.progress((idx + 1) / len(ids_to_process))
            
            st.success("Batch Scrape Complete!")
            st.rerun()

# ==========================================
# 2. ENCYCLOPEDIA TAB (The Sleek Table)
# ==========================================
with tab_encyclo:
    if df.empty:
        st.info("No data found. Start by scraping some IDs!")
    else:
        # Quick Statistics Header
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Novels", len(df))
        m2.metric("Adult Content", len(df[df['is_19'] == 1]))
        m3.metric("Plus Content", len(df[df['is_plus'] == 1]))
        m4.metric("Avg Chapters", int(df['chapters'].mean()) if not df.empty else 0)

        # Search
        search = st.text_input("🔍 Search Titles or Authors", "").lower()
        display_df = df.copy()
        if search:
            display_df = display_df[
                display_df['title'].str.lower().str.contains(search) | 
                display_df['writer'].str.lower().str.contains(search)
            ]

        # Formatting for display
        display_df['id'] = display_df['id'].astype(str) # No commas
        
        st.dataframe(
            display_df[['id', 'title', 'writer', 'chapters', 'views', 'is_19', 'is_plus', 'is_completed', 'url']],
            column_config={
                "id": "ID",
                "title": st.column_config.TextColumn("Title", width="medium"),
                "writer": "Author",
                "chapters": "Ch.",
                "views": st.column_config.NumberColumn("Views", format="%d"),
                "is_19": st.column_config.CheckboxColumn("18+🔞"),
                "is_plus": st.column_config.CheckboxColumn("Plus💎"),
                "is_completed": st.column_config.CheckboxColumn("Done✅"),
                "url": st.column_config.LinkColumn("Link", display_text="Open ↗")
            },
            hide_index=True,
            use_container_width=True
        )

# ==========================================
# 3. TAG MANAGER (The Tag Engine)
# ==========================================
with tab_tags:
    if df.empty:
        st.info("Archive some novels to see tag analytics.")
    else:
        st.header("🏷️ English Tag Analysis")
        
        # Flatten tags list
        all_tags = [tag for sublist in df['tags_en'] for tag in sublist]
        tag_counts = pd.Series(all_tags).value_counts().reset_index()
        tag_counts.columns = ['Tag Name', 'Count']

        tag_search = st.text_input("Filter Tag List...", "")
        if tag_search:
            tag_counts = tag_counts[tag_counts['Tag Name'].str.contains(tag_search, case=False)]

        col_t1, col_t2 = st.columns([1, 2])
        
        with col_t1:
            st.subheader("Top Tags")
            st.dataframe(tag_counts.head(15), hide_index=True, use_container_width=True)
            
        with col_t2:
            st.subheader("Distribution")
            st.dataframe(
                tag_counts,
                column_config={
                    "Count": st.column_config.ProgressColumn("Frequency", min_value=0, max_value=int(tag_counts['Count'].max()))
                },
                hide_index=True,
                use_container_width=True
            )
