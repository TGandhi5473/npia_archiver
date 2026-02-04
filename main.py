import streamlit as st
import pandas as pd
from core.database import NovelDB
from core.scraper import NovelpiaScraper
import plotly.express as px

# --- SETUP ---
st.set_page_config(page_title="Sleeper Scout 2026", layout="wide")
db = NovelDB()
scraper = NovelpiaScraper(db)

# --- SIDEBAR: MISSION PARAMETERS ---
with st.sidebar:
    st.header("🎯 Recon Settings")
    
    # 1. Mass Scout Range
    st.subheader("Mass Recon")
    start_id = st.number_input("Start ID", value=383000)
    end_id = st.number_input("End ID", value=383100)
    
    if st.button("🚀 Execute Mass Scout"):
        progress_bar = st.progress(0)
        status = st.empty()
        total = end_id - start_id + 1
        
        for i, nid in enumerate(range(int(start_id), int(end_id) + 1)):
            status.text(f"Scanning: {nid}")
            res = scraper.scrape_novel(str(nid))
            progress_bar.progress((i + 1) / total)
            if "2FA" in res:
                st.warning("⚠️ 2FA / Login Wall Detected.")
                break
        st.success("Mission Complete.")

    st.divider()
    
    # 2. Results Filtering (Applied to Intelligence Vault)
    st.subheader("Display Filters")
    f_plus = st.checkbox("Plus Only", value=False)
    f_19 = st.checkbox("18+ Only", value=False)
    
    # Garbage Dump
    if st.button("🗑️ Dump Blacklist (Clear Garbage)"):
        db.clear_blacklist()
        st.toast("Blacklist purged.")

# --- MAIN UI ---
st.title("🛡️ Sleeper Scout Intelligence")

tab1, tab2, tab3 = st.tabs(["Intelligence Vault", "Tag Analytics", "Manual Entry"])

# --- TAB 1: INTELLIGENCE VAULT (All novels by default) ---
with tab1:
    conn = db.get_connection()
    df = pd.read_sql("SELECT * FROM valid_novels", conn)
    
    if not df.empty:
        # Filtering logic: only narrows down if boxes are checked
        if f_plus:
            df = df[df['is_plus'] == 1]
        if f_19:
            df = df[df['is_19'] == 1]
            
        st.dataframe(
            df.sort_values(by="ratio", ascending=False),
            column_config={
                "url": st.column_config.LinkColumn("Access"),
                "ratio": st.column_config.NumberColumn("Ratio", format="%.2f ⭐"),
                "is_19": st.column_config.CheckboxColumn("18+"),
                "is_plus": st.column_config.CheckboxColumn("Plus")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Vault is empty. Execute a mission in the sidebar.")

# --- TAB 2: GLOBAL TAG TRACKER ---
with tab2:
    st.subheader("🏷️ Global Genre Analysis")
    tag_counts = db.get_tag_stats()
    
    if tag_counts:
        # Convert counter to DataFrame
        tag_df = pd.DataFrame(tag_counts.items(), columns=['Tag', 'Frequency']).sort_values('Frequency', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(tag_df.head(20), x='Tag', y='Frequency', 
                         title="Top 20 Trending Tags",
                         color='Frequency', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.write("### Raw Tag Counts")
            st.dataframe(tag_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No tag data available yet.")

# --- TAB 3: MANUAL ENTRY ---
with tab3:
    target_id = st.text_input("Enter Specific Novel ID to Test")
    if st.button("Run Surgical Scout"):
        with st.spinner("Scraping..."):
            result = scraper.scrape_novel(target_id)
            st.write(result)
