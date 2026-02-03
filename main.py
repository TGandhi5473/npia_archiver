# ==========================================
# FILE: main.py
# ==========================================
import streamlit as st
import pandas as pd
from core.scraper import NovelArchiver

# --- Page Config ---
st.set_page_config(page_title="NPIA Encyclopedia", layout="wide", page_icon="📚")

# --- Initialize Session State ---
if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

# --- Sidebar Filters ---
with st.sidebar:
    st.title("⚙️ Global Filters")
    exclude_19 = st.checkbox("Hide 18+ Content 🔞", value=False)
    only_plus = st.checkbox("Only Plus Content 💎", value=False)
    only_completed = st.checkbox("Only Completed ✅", value=False)
    
    st.divider()
    if st.button("🔄 Refresh Data"):
        st.rerun()

# --- Load Data ---
df = st.session_state.archiver.db.get_all_novels_df()

if df.empty:
    st.warning("Archive is empty. Go to the Scraper tab to add novels!")
else:
    # Apply Sidebar Filters to the global dataframe
    if exclude_19:
        df = df[df['is_19'] == 0]
    if only_plus:
        df = df[df['is_plus'] == 1]
    if only_completed:
        df = df[df['is_completed'] == 1]

    # --- Tabs ---
    tab_scrape, tab_encyclo, tab_tags = st.tabs(["🚀 Scraper", "🔍 Encyclopedia", "🏷️ Tag Manager"])

    # 1. SCRAPER TAB
    with tab_scrape:
        st.header("Novelpia Scraper")
        novel_id_input = st.text_input("Enter Novel ID(s)", placeholder="e.g. 123456, 789012")
        
        if st.button("Start Archiving"):
            ids = [i.strip() for i in novel_id_input.split(',') if i.strip()]
            progress_bar = st.progress(0)
            for idx, nid in enumerate(ids):
                result = st.session_state.archiver.scrape_novel(nid)
                st.write(f"ID {nid}: {result}")
                progress_bar.progress((idx + 1) / len(ids))
            st.success("Scraping Complete!")

    # 2. ENCYCLOPEDIA TAB
    with tab_encyclo:
        st.header("Novel Encyclopedia")
        
        # Search Bar
        search_query = st.text_input("Search by Title or Author", "").lower()
        if search_query:
            df = df[df['title'].str.lower().str.contains(search_query) | 
                    df['writer'].str.lower().str.contains(search_query)]

        # Prepare Display DF
        display_df = df.copy()
        display_df['id'] = display_df['id'].astype(str) # Remove numeric commas
        
        st.dataframe(
            display_df[['id', 'title', 'writer', 'chapters', 'views', 'is_19', 'is_plus', 'is_completed', 'url']],
            column_config={
                "id": "ID",
                "title": "Title",
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
        st.caption(f"Showing {len(df)} novels.")

    # 3. TAG MANAGER TAB
    with tab_tags:
        st.header("Global Tag Explorer")
        
        # Flatten all English tags and count them
        all_tags = [tag for sublist in df['tags_en'] for tag in sublist]
        if all_tags:
            tag_counts = pd.Series(all_tags).value_counts().reset_index()
            tag_counts.columns = ['Tag Name', 'Novels Count']

            # Searchable Tag Table
            tag_search = st.text_input("Find a tag...", "")
            if tag_search:
                tag_counts = tag_counts[tag_counts['Tag Name'].str.contains(tag_search, case=False)]

            st.write(f"Identified {len(tag_counts)} unique English tags.")
            
            # Split into two columns: Most Popular vs List
            col_top, col_list = st.columns([1, 2])
            
            with col_top:
                st.subheader("🔥 Top 10 Tags")
                st.table(tag_counts.head(10))
                
            with col_list:
                st.subheader("All English Tags")
                st.dataframe(
                    tag_counts,
                    column_config={"Novels Count": st.column_config.ProgressColumn("Frequency", format="%d", min_value=0, max_value=int(tag_counts['Novels Count'].max()))},
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("No tags found in the database yet.")
