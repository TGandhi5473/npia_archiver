import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import translate_tags, TAG_MAP

# 1. Setup & Config
st.set_page_config(page_title="Sleeper Scout", layout="wide", page_icon="🎯")
db = NovelDB()
scraper = NovelpiaScraper(db)

# 2. Sidebar - Mass Recon Control
with st.sidebar:
    st.header("🚀 Mass Recon")
    st.info("Scouting as Guest (No Cookies)")
    s_id = st.number_input("Start ID", value=383000, step=1)
    e_id = st.number_input("End ID", value=383020, step=1)
    
    if st.button("Start Global Scan"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        id_range = range(int(s_id), int(e_id) + 1)
        total = len(id_range)
        
        for i, nid in enumerate(id_range):
            status_text.text(f"Scanning ID: {nid}...")
            scraper.scrape_novel(str(nid))
            progress_bar.progress((i + 1) / total)
        
        status_text.text("✅ Recon Mission Complete!")
        st.balloons()

# 3. Main Dashboard Tabs
t1, t2, t3 = st.tabs(["🏛️ The Vault", "📊 Market Analytics", "🔬 Surgical Scout"])

with t1:
    st.subheader("Intelligence Database")
    # Fetch all data from the updated SQLite table
    df = pd.read_sql("SELECT * FROM valid_novels", db.get_connection())
    
    if not df.empty:
        # Translate Korean tags to English for the UI
        df['tags_en'] = df['tags'].apply(translate_tags)
        
        # Reorder columns for better readability
        cols = ['novel_id', 'title', 'ratio', 'fav', 'ep', 'views', 'recs', 'tags_en', 'is_plus', 'is_19']
        display_df = df[cols].sort_values("ratio", ascending=False)
        
        # Interactive Table
        st.dataframe(
            display_df,
            column_config={
                "url": st.column_config.LinkColumn("Link"),
                "ratio": st.column_config.NumberColumn("Sleeper Ratio", format="%.2f ⭐"),
                "is_plus": st.column_config.CheckboxColumn("Plus?"),
                "is_19": st.column_config.CheckboxColumn("19+?"),
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("The Vault is empty. Run a Mass Recon from the sidebar to gather data.")

with t2:
    st.subheader("Genre & Trope Distribution")
    stats = db.get_tag_stats()
    if stats:
        # Map Korean tags to English for the Chart
        en_stats = {TAG_MAP.get(k, k): v for k, v in stats.items()}
        tag_df = pd.DataFrame(en_stats.items(), columns=['Tag', 'Count']).sort_values('Count', ascending=False)
        
        c1, c2 = st.columns(2)
        with c1:
            fig_pie = px.pie(tag_df.head(15), values='Count', names='Tag', hole=0.4, title="Dominant Tags (Top 15)")
            st.plotly_chart(fig_pie, use_container_width=True)
        with c2:
            fig_bar = px.bar(tag_df.head(15), x='Count', y='Tag', orientation='h', title="Tag Frequency")
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No tag data available yet.")

with t3:
    st.subheader("Individual ID Validation")
    tid = st.text_input("Enter Novel ID for deep analysis", placeholder="e.g. 351285")
    if st.button("Run Diagnostic"):
        with st.spinner("Intercepting data..."):
            result = scraper.scrape_novel(tid, return_raw=True)
            st.json(result)
