import streamlit as st
import os
from core.scraper import NovelArchiver

# 1. Initialize the Archiver once and keep it in memory
if 'archiver' not in st.session_state:
    st.session_state.archiver = NovelArchiver()

st.title("📖 Novelpia Archiver v2.0")

# Sidebar Metrics
total_archived = len(st.session_state.archiver.data)
st.sidebar.metric("Saved in JSON", total_archived)

# UI Controls
col1, col2 = st.columns(2)
with col1:
    start_id = st.number_input("Start ID", value=402000)
with col2:
    end_id = st.number_input("End ID", value=402010)

if st.button("🚀 Start Archiving"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    log_area = st.container()
    
    total_range = end_id - start_id + 1
    
    for i, novel_id in enumerate(range(start_id, end_id + 1)):
        # Calculate progress
        pct = (i + 1) / total_range
        progress_bar.progress(pct)
        status_text.text(f"Processing ID: {novel_id}...")

        # CALL THE SCRAPER
        # This updates self.data and calls _save() automatically
        result = st.session_state.archiver.scrape_novel(novel_id)
        
        # Display live feedback in UI
        with log_area:
            if result == "Saved":
                st.success(f"✅ {novel_id}: Saved to JSON")
            elif result == "Filtered":
                st.warning(f"⏳ {novel_id}: Filtered (Low Quality)")
            elif result == "Cached":
                st.info(f"📦 {novel_id}: Already in Archive")
            else:
                st.error(f"❌ {novel_id}: {result}")

    st.balloons()
    st.success(f"Finished! Total archived is now: {len(st.session_state.archiver.data)}")

# Debug: Show the actual file path where it's saving
st.divider()
abs_path = os.path.abspath(st.session_state.archiver.storage_path)
st.caption(f"Saving to: `{abs_path}`")
