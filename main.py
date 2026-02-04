import streamlit as st
import pandas as pd
from datetime import datetime
from core.database import NovelDB
from core.scraper import NovelpiaScraper

st.set_page_config(page_title="NPIA Sleeper Scout", layout="wide", page_icon="🕵️")

# --- INITIALIZATION ---
if 'db' not in st.session_state: st.session_state.db = NovelDB()
if 'scraper' not in st.session_state: st.session_state.scraper = NovelpiaScraper(st.session_state.db)

# --- DIALOGS (2nd confirmation gate) ---
@st.dialog("🔥 CONFIRM FULL PURGE")
def nuke_vault_dialog():
    st.warning("All identified Sleeper hits will be permanently erased. Blacklist will remain.")
    st.write("Do you want to proceed?")
    col1, col2 = st.columns(2)
    if col1.button("YES, NUKE IT", type="primary", use_container_width=True):
        st.session_state.db.clear_vault()
        st.rerun()
    if col2.button("NO, GO BACK", use_container_width=True):
        st.rerun()

# --- SIDEBAR ---
with st.sidebar:
    st.title("🕵️ Scout Analyst")
    df_raw = pd.read_sql("SELECT * FROM valid_novels", st.session_state.db.get_connection())
    st.metric("Vault Capacity", len(df_raw))
    
    st.divider()
    min_ratio = st.slider("Min Ratio Filter", 0.0, 50.0, 10.0)
    hide_19 = st.checkbox("Hide 18+ Novels", value=False)
    
    # --- DANGER ZONE (1st confirmation gate) ---
    st.divider()
    with st.popover("🗑️ Clear Vault", use_container_width=True):
        st.write("First confirmation: Are you sure?")
        if st.button("Initiate Wipe", type="primary"):
            nuke_vault_dialog()

# --- MAIN TABS ---
tab_scout, tab_vault = st.tabs(["🚀 Mission Control", "📚 Intelligence Vault"])

with tab_scout:
    st.subheader("Targeting Parameters")
    c1, c2 = st.columns(2)
    start = c1.number_input("Start ID", value=450000)
    end = c2.number_input("End ID", value=450100)
    
    # Stable scrolling window
    log_window = st.container(height=350, border=True)
    
    if st.button("▶️ START SWEEP", type="primary", use_container_width=True):
        for nid in range(int(start), int(end) + 1):
            status = st.session_state.scraper.scrape_novel(nid)
            log_window.code(f"[{datetime.now().strftime('%H:%M:%S')}] ID {nid}: {status}")
        st.success("Sweep finished!")
        st.rerun()

with tab_vault:
    if not df_raw.empty:
        # Filter logic
        filtered_df = df_raw[df_raw['ratio'] >= min_ratio]
        if hide_19:
            filtered_df = filtered_df[filtered_df['is_19'] == 0]
            
        st.dataframe(
            filtered_df.sort_values("ratio", ascending=False), 
            use_container_width=True, 
            height=600
        )
    else:
        st.info("The Vault is empty. Launch a mission to find some sleepers.")
