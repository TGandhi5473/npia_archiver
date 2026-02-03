# ==========================================
# FILE: main.py
# ==========================================
import streamlit as st
from core.scraper import NovelArchiver

if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

st.set_page_config(page_title="NPIA Archiver", layout="wide")
tab1, tab2 = st.tabs(["🚀 Scraper", "🔍 Encyclopedia"])

with tab1:
    st.title("Novelpia Archiver")
    # ... (Your existing Scraper UI code here) ...

with tab2:
    df = st.session_state.archiver.db.get_all_novels_df()
    if df.empty:
        st.info("Archive is empty.")
    else:
        # Polish for display
        display_df = df.copy()
        display_df['id'] = display_df['id'].astype(str) # Remove commas
        display_df['tags_display'] = display_df['tags_en'].apply(lambda x: ", ".join(x))
        
        st.dataframe(
            display_df[['id', 'title', 'writer', 'chapters', 'views', 'tags_display', 'is_19', 'is_plus', 'is_completed', 'url']],
            column_config={
                "id": "ID",
                "is_19": st.column_config.CheckboxColumn("19+🔞"),
                "is_plus": st.column_config.CheckboxColumn("Plus💎"),
                "is_completed": st.column_config.CheckboxColumn("Done✅"),
                "url": st.column_config.LinkColumn("Link", display_text="Open ↗")
            },
            hide_index=True, use_container_width=True
        )
