import streamlit as st
import pandas as pd
from core.database import NovelDB
from core.scraper import NovelpiaScraper
import plotly.express as px

# --- SETUP ---
st.set_page_config(page_title="Sleeper Scout 2026", layout="wide")
db = NovelDB()
scraper = NovelpiaScraper(db)

# --- SIDEBAR: TAG LEADERBOARD ---
with st.sidebar:
    st.header("🏷️ Global Tag Stats")
    tag_counts = db.get_tag_stats()
    if tag_counts:
        # Create a mini leaderboard
        tag_df = pd.DataFrame(tag_counts.items(), columns=['Tag', 'Count']).sort_values('Count', ascending=False)
        st.bar_chart(tag_df.set_index('Tag').head(10)) # Top 10 tags
        
        # Tag Filter Dropdown
        unique_tags = ["All"] + sorted(list(tag_counts.keys()))
        selected_tag = st.selectbox("Filter by Tag", unique_tags)
    else:
        st.info("No tags scouted yet.")
        selected_tag = "All"

# --- MAIN UI ---
st.title("🚀 Sleeper Scout: Novelpia")

tab1, tab2 = st.tabs(["Mission Control", "Intelligence Vault"])

with tab1:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Manual Recon")
        novel_id = st.text_input("Novel ID (e.g., 383628)")
        if st.button("Scout Target"):
            with st.spinner("Penetrating Novelpia..."):
                result = scraper.scrape_novel(novel_id)
                st.toast(result)

with tab2:
    st.subheader("📊 Analyzed Intelligence")
    
    # Load and Filter Data
    conn = db.get_connection()
    df = pd.read_sql("SELECT * FROM valid_novels", conn)
    
    if not df.empty:
        # Apply Tag Filter
        if selected_tag != "All":
            df = df[df['tags'].str.contains(selected_tag, na=False)]
            
        # Styling: Highlight high ratios
        def highlight_sleepers(val):
            color = 'background-color: #004d00' if val > 30 else ''
            return color

        styled_df = df.style.map(highlight_sleepers, subset=['ratio'])
        
        st.dataframe(
            styled_df,
            column_config={
                "url": st.column_config.LinkColumn("Link"),
                "ratio": st.column_config.NumberColumn("Ratio", format="%.2f ⭐"),
                "is_19": st.column_config.CheckboxColumn("18+"),
                "is_plus": st.column_config.CheckboxColumn("Plus")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.warning("The Vault is empty. Start scouting IDs to gather data.")
