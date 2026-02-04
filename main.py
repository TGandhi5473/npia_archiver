import streamlit as st
import pandas as pd
from core.database import NovelDB
from core.scraper import NovelpiaScraper

# --- SETUP ---
st.set_page_config(page_title="Sleeper Scout 2026", layout="wide")
db = NovelDB()
scraper = NovelpiaScraper(db)

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header("🎯 Target Filters")
    
    # Range of Novel IDs for Testing
    st.subheader("Mass Recon")
    start_id = st.number_input("Start ID", value=383000)
    end_id = st.number_input("End ID", value=383100)
    
    if st.button("🚀 Execute Mass Scout"):
        status_box = st.empty()
        for nid in range(int(start_id), int(end_id) + 1):
            status_box.info(f"Scanning Target: {nid}...")
            res = scraper.scrape_novel(str(nid))
            if "2FA" in res: # Detection for 2FA trigger
                st.warning(f"⚠️ 2FA Triggered on {nid}! Check terminal/prompt.")
                break 
        st.success("Recon Mission Complete.")

    st.divider()
    
    # Result Filters (Default: All)
    st.subheader("Intelligence Filters")
    f_plus = st.checkbox("Show Only 'Plus' Works", value=False)
    f_19 = st.checkbox("Show Only '18+' Content", value=False)
    
    if st.button("🗑️ Dump Trash (Clear Blacklist)"):
        db.clear_blacklist() # New method below
        st.toast("Blacklist Purged.")

# --- MAIN UI: INTELLIGENCE VAULT ---
st.title("🛡️ Sleeper Scout Vault")

# Fetch Data
conn = db.get_connection()
df = pd.read_sql("SELECT * FROM valid_novels", conn)

if not df.empty:
    # 1. Apply Logic: Filters only apply if checked
    if f_plus:
        df = df[df['is_plus'] == 1]
    if f_19:
        df = df[df['is_19'] == 1]

    # 2. Display Table
    st.dataframe(
        df.sort_values(by="ratio", ascending=False),
        column_config={
            "url": st.column_config.LinkColumn("Access"),
            "ratio": st.column_config.NumberColumn("Sleeper Ratio", format="%.2f ⭐"),
            "is_19": st.column_config.CheckboxColumn("18+"),
            "is_plus": st.column_config.CheckboxColumn("Plus")
        },
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No intelligence gathered. Use the sidebar to scout IDs.")
