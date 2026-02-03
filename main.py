import streamlit as st
import pandas as pd
from core.scraper import NovelArchiver
from core.translator import identify_missing_tags, TAG_MAP

# Initialize the backend logic
archiver = NovelArchiver()

st.set_page_config(page_title="Novelpia Archiver", layout="wide")

st.title("📚 Novelpia Metadata Archiver")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("Scraper Settings")
start_id = st.sidebar.number_input("Start ID", value=402000)
end_id = st.sidebar.number_input("End ID", value=403000)

if st.sidebar.button("🚀 Start Scraping"):
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    consecutive_404s = 0
    total_to_check = end_id - start_id + 1
    
    for i, nid in enumerate(range(start_id, end_id + 1)):
        result = archiver.scrape_novel(nid)
        
        # Auto-stop logic
        if result == "404":
            consecutive_404s += 1
        else:
            consecutive_404s = 0
            
        if consecutive_404s >= 10:
            st.warning("Stopped: Hit 10 consecutive 404s.")
            break
            
        # Update UI
        progress = (i + 1) / total_to_check
        progress_bar.progress(progress)
        status_text.text(f"Processing ID {nid}: {result}")

# --- MAIN DASHBOARD ---
tab1, tab2 = st.tabs(["📊 Archived Data", "🏷️ Tag Manager"])

with tab1:
    if archiver.data:
        df = pd.DataFrame.from_dict(archiver.data, orient='index')
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data archived yet. Use the sidebar to start.")

with tab2:
    missing = identify_missing_tags(archiver.data)
    if missing:
        st.write("### New Tags Found (Needs Translation):")
        st.code(", ".join(missing))
    else:
        st.success("All tags are currently mapped to English!")
