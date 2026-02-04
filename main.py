import sys
import asyncio
import streamlit as st
import pandas as pd
from datetime import datetime
from core.database import NovelDB
from core.scraper import NovelpiaScraper

# Fix for Windows Async loops - Vital for 2026 subprocess handling
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="NPIA Sleeper Scout", layout="wide", page_icon="🕵️")

# --- CUSTOM CSS FOR GITHUB LOOK ---
st.markdown("""
    <style>
    .gh-card { border: 1px solid #d0d7de; border-radius: 6px; padding: 16px; background: #ffffff; margin-bottom: 12px; }
    .gh-title { color: #0969da; font-weight: 600; font-size: 1.1rem; text-decoration: none; }
    .gh-tag { background: #f1f8ff; color: #0366d6; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; border: 1px solid #c8e1ff; }
    .ratio-badge { float: right; background: #dafbe1; color: #1a7f37; padding: 2px 12px; border-radius: 20px; font-weight: bold; }
    .stCodeBlock { border: 1px solid #d0d7de !important; }
    </style>
""", unsafe_allow_html=True)

# --- INIT STATE ---
if 'db' not in st.session_state: 
    st.session_state.db = NovelDB()
if 'scraper' not in st.session_state: 
    st.session_state.scraper = NovelpiaScraper(st.session_state.db)

# --- SIDEBAR: DYNAMIC INTELLIGENCE ---
with st.sidebar:
    st.header("📊 Intelligence Report")
    # Fetch raw data for metrics and filtering
    df_raw = pd.read_sql("SELECT * FROM valid_novels", st.session_state.db.get_connection())
    st.metric("Total Qualified Novels", len(df_raw))
    
    st.divider()
    st.subheader("🎯 Sleeper Tuning")
    # This allows you to set the 'Sleeper Hit' bar after scraping quality data
    ratio_threshold = st.slider("Minimum Sleeper Ratio (Fav/Ep)", 0.0, 20.0, 8.0, help="High ratio = Hidden Gem potential")
    min_episodes = st.number_input("Min Chapters to Consider", value=10)
    
    st.divider()
    st.subheader("🔍 Global Filters")
    hide_19 = st.checkbox("Hide Adult (19+) 🔞")
    plus_only = st.checkbox("Plus Only 💎")

# --- TABS ---
tab_scout, tab_vault = st.tabs(["🚀 Scout Missions", "📚 The Encyclopedia"])

with tab_scout:
    st.info("Quality Gate: Scraper will automatically skip novels with < 50 Favorites or < 5 Chapters.")
    c1, c2 = st.columns(2)
    start_id = c1.number_input("Start ID", value=450000, step=1)
    end_id = c2.number_input("End ID", value=450100, step=1)
    
    if st.button("▶️ Launch Scouting Mission", type="primary", use_container_width=True):
        # 1. FIXED-HEIGHT ROLLING WINDOW (The Scroll Fix)
        # This prevents the page from jumping while thousands of IDs are processed
        log_window = st.container(height=300, border=True)
        
        with st.status("Gathering Intel...", expanded=True) as status:
            rolling_logs = []
            for nid in range(int(start_id), int(end_id) + 1):
                status.write(f"Probing ID {nid}...")
                result = st.session_state.scraper.scrape_novel(nid)
                
                # 2. Update Rolling Log Buffer (Maintains fixed window size)
                timestamp = datetime.now().strftime('%H:%M:%S')
                log_entry = f"[{timestamp}] ID {nid}: {result}"
                rolling_logs.append(log_entry)
                
                # Keep only the last 50 logs in the rolling window for performance
                log_window.code("\n".join(rolling_logs[-50:]))
                
                # Safety break for connection issues
                if "BLOCKED" in result or "403" in result:
                    st.error("Firewall detection active. Aborting mission.")
                    break
                    
            status.update(label="Scouting Complete", state="complete", expanded=False)
        st.toast("Intelligence Updated!")
        st.rerun()

with tab_vault:
    if not df_raw.empty:
        # 3. APPLY POST-SCRAPE SLEEPER LOGIC
        df = df_raw.copy()
        
        # Quality Masks
        mask = (df['ratio'] >= ratio_threshold) & (df['ep'] >= min_episodes)
        if hide_19: mask &= (df['is_19'] == 0)
        if plus_only: mask &= (df['is_plus'] == 1)
        
        df_sleepers = df[mask].sort_values("ratio", ascending=False)
        
        st.subheader(f"Found {len(df_sleepers)} Sleeper Hits matching your threshold")
        
        for _, row in df_sleepers.iterrows():
            st.markdown(f"""
                <div class="gh-card">
                    <span class="ratio-badge">{row['ratio']} Ratio</span>
                    <a class="gh-title" href="{row['url']}" target="_blank">{row['title']}</a><br>
                    <small>by <b>{row['author']}</b> • {row['ep']} chapters • {row['fav']} favorites</small>
                    <div style="margin-top:10px;">
                        {" ".join([f'<span class="gh-tag">{t.strip()}</span>' for t in str(row['tags']).split(',')[:5]])}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("The Vault is empty. Run a Scout Mission to find hidden gems.")
