import streamlit as st
import pandas as pd
from core.database import NovelDB
from core.scraper import NovelpiaScraper
import plotly.express as px

# --- SETUP ---
st.set_page_config(page_title="Sleeper Scout 2026", layout="wide")
db = NovelDB()
scraper = NovelpiaScraper(db)

# --- SIDEBAR: MISSION CONTROL ---
with st.sidebar:
    st.header("🎯 Mission Parameters")
    
    # 1. Mass Scout Configuration
    st.subheader("Mass Reconnaissance")
    col_s, col_e = st.columns(2)
    start_id = col_s.number_input("Start ID", value=383000)
    end_id = col_e.number_input("End ID", value=383100)
    
    if st.button("🚀 Launch Scout Mission", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        total_tasks = int(end_id - start_id + 1)
        
        for i, nid in enumerate(range(int(start_id), int(end_id) + 1)):
            status_text.text(f"Scanning Target: {nid}...")
            result = scraper.scrape_novel(str(nid))
            progress_bar.progress((i + 1) / total_tasks)
            if "2FA" in result:
                st.error("2FA Wall Detected. Mission Aborted.")
                break
        st.success("Recon mission completed.")

    st.divider()
    
    # 2. Filtering Logic (Defaults to showing everything)
    st.subheader("Intelligence Filters")
    f_plus = st.checkbox("Plus Only", value=False)
    f_19 = st.checkbox("18+ Only", value=False)
    
    # Garbage Management
    if st.button("🗑️ Purge Blacklist (Retry Garbage)"):
        db.clear_blacklist()
        st.toast("Blacklist wiped. You can now re-scout failed IDs.")

# --- MAIN UI TABS ---
st.title("🛡️ Sleeper Scout Dashboard")

tab_vault, tab_tags, tab_surgical = st.tabs([
    "📂 Intelligence Vault", 
    "📊 Global Tag Analytics", 
    "🔬 Surgical Entry"
])

# --- TAB 1: THE VAULT ---
with tab_vault:
    conn = db.get_connection()
    df = pd.read_sql("SELECT * FROM valid_novels", conn)
    
    if not df.empty:
        # Filter Logic: Data is only removed if the user explicitly checks the box
        if f_plus:
            df = df[df['is_plus'] == 1]
        if f_19:
            df = df[df['is_19'] == 1]
            
        st.dataframe(
            df.sort_values(by="ratio", ascending=False),
            column_config={
                "url": st.column_config.LinkColumn("Access"),
                "ratio": st.column_config.NumberColumn("Sleeper Ratio", format="%.2f ⭐"),
                "is_19": st.column_config.CheckboxColumn("18+"),
                "is_plus": st.column_config.CheckboxColumn("Plus"),
                "last_updated": st.column_config.DatetimeColumn("Scouted At")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("The vault is empty. Start a 'Mass Recon' mission in the sidebar to gather intelligence.")

# --- TAB 2: TAG ANALYTICS ---
with tab_tags:
    st.subheader("🏷️ Global Market Saturation")
    tag_counts = db.get_tag_stats()
    
    if tag_counts:
        tag_df = pd.DataFrame(tag_counts.items(), columns=['Tag', 'Frequency']).sort_values('Frequency', ascending=False)
        
        c1, c2 = st.columns([3, 2])
        with c1:
            # Interactive Bar Chart
            fig = px.bar(tag_df.head(15), x='Tag', y='Frequency', 
                         title="Top 15 Most Common Tags",
                         color='Frequency', color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.write("### Tag Leaderboard")
            st.dataframe(tag_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No tags detected yet. Data will populate here once novels are scouted.")

# --- TAB 3: SURGICAL ENTRY ---
with tab_surgical:
    st.subheader("Manual ID Recon")
    target_id = st.text_input("Target Novel ID", help="Enter a specific ID to bypass the queue.")
    if st.button("Surgical Scout"):
        with st.spinner(f"Analyzing {target_id}..."):
            res = scraper.scrape_novel(target_id)
            st.code(res)
