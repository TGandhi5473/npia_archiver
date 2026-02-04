import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import TAG_MAP

# 1. Page Configuration
st.set_page_config(page_title="NPIA Sleeper Scout", layout="wide", page_icon="🎯")
db = NovelDB()
scraper = NovelpiaScraper(db)

# 2. Sidebar - Recon Controls
with st.sidebar:
    st.header("🚀 Recon Mission")
    st.info("Mode: Hail Mary (Guest)")
    
    start_id = st.number_input("Start ID", value=383000, step=1)
    end_id = st.number_input("End ID", value=383020, step=1)
    
    if st.button("Launch Mass Recon"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        id_range = range(int(start_id), int(end_id) + 1)
        total = len(id_range)
        
        for i, nid in enumerate(id_range):
            status_text.text(f"Scanning ID: {nid}...")
            # Use the scraper function you provided
            result = scraper.scrape_novel(str(nid))
            progress_bar.progress((i + 1) / total)
            
        status_text.text("✅ Mission Complete!")
        st.balloons()
    
    st.divider()
    st.header("⚙️ Database Tools")
    if st.button("Clear Blacklist"):
        if db.clear_blacklist():
            st.success("Blacklist wiped clean!")
    
    if st.button("🚨 Reset Vault", type="primary"):
        if db.clear_vault():
            st.success("Vault is empty. Database clean.")

# 3. Main Interface Tabs
t1, t2, t3 = st.tabs(["🏛️ The Vault", "📊 Market Analytics", "🔬 Surgical Scout"])

with t1:
    st.subheader("Intelligence Database")
    
    # Load data from updated database
    try:
        df = pd.read_sql("SELECT * FROM valid_novels", db.get_connection())
    except Exception as e:
        df = pd.DataFrame()
        st.error(f"Database sync error: {e}")

    if not df.empty:
        # Define display columns to match your new database structure
        # Order: ID, Title, Ratio (Priority), then the raw numbers
        cols = ['novel_id', 'title', 'ratio', 'fav', 'ep', 'al', 'views', 'recs', 'tags', 'is_plus', 'is_19']
        
        # Sort by Ratio as default (Sleeper identification)
        display_df = df[cols].sort_values("ratio", ascending=False)
        
        st.dataframe(
            display_df,
            column_config={
                "url": st.column_config.LinkColumn("Link"),
                "ratio": st.column_config.NumberColumn("Sleeper Ratio", format="%.2f ⭐"),
                "is_plus": st.column_config.CheckboxColumn("Plus?"),
                "is_19": st.column_config.CheckboxColumn("18+?"),
                "views": st.column_config.NumberColumn("Total Views", format="%d 👁️"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("The Vault is empty. Gather data using the Recon controls in the sidebar.")

with t2:
    st.subheader("Trope & Tag Distribution")
    stats = db.get_tag_stats()
    
    if stats:
        # Prepare data for Charting
        tag_data = pd.DataFrame(stats.items(), columns=['Tag', 'Count']).sort_values('Count', ascending=False)
        
        # Create a Bar Chart of top 20 tags
        fig = px.bar(tag_data.head(20), x='Count', y='Tag', orientation='h', 
                     title="Most Common Tags", color='Count', color_continuous_scale='Viridis')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics available yet. Scan more novels!")

with t3:
    st.subheader("Individual ID Analysis")
    tid = st.text_input("Enter ID (e.g., 351285)", placeholder="351285")
    if st.button("Run Diagnostic"):
        with st.spinner("Decoding metadata..."):
            # This calls the scraper without saving to DB so you can see raw results
            analysis = scraper.scrape_novel(tid, return_raw=True)
            if isinstance(analysis, dict):
                st.success(f"Analysis for: {analysis.get('title')}")
                st.json(analysis)
            else:
                st.error(f"Scraper returned: {analysis}")
