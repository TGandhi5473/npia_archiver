import sys, asyncio, streamlit as st, pandas as pd
from datetime import datetime
from core.database import NovelDB
from core.scraper import NovelpiaScraper # Assuming your scraper class name

# Fix for Windows Async loops
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
    </style>
""", unsafe_allow_html=True)

# --- INIT STATE ---
if 'db' not in st.session_state: st.session_state.db = NovelDB()
if 'scraper' not in st.session_state: st.session_state.scraper = NovelpiaScraper(st.session_state.db)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📊 Intelligence Report")
    df_raw = pd.read_sql("SELECT * FROM valid_novels", st.session_state.db.get_connection())
    st.metric("Identified Sleepers", len(df_raw))
    st.divider()
    st.subheader("Filter Encyclopedia")
    hide_19 = st.checkbox("Hide Adult (19+) 🔞")
    plus_only = st.checkbox("Plus Only 💎")

# --- TABS ---
tab_scout, tab_vault = st.tabs(["🚀 Scout Missions", "📚 The Encyclopedia"])

with tab_scout:
    c1, c2 = st.columns(2)
    start_id = c1.number_input("Start ID", value=450000)
    end_id = c2.number_input("End ID", value=450010)
    
    if st.button("▶️ Launch Scouting Mission", type="primary", use_container_width=True):
        log_window = st.empty()
        rolling_logs = []
        
        with st.status("Gathering Intel...", expanded=True) as status:
            for nid in range(int(start_id), int(end_id) + 1):
                status.write(f"Probing ID {nid}...")
                result = st.session_state.scraper.scrape_novel(nid)
                
                # Rolling Log Logic (Last 8 entries)
                log_entry = f"[{datetime.now().strftime('%H:%M:%S')}] ID {nid}: {result}"
                rolling_logs.append(log_entry)
                if len(rolling_logs) > 8: rolling_logs.pop(0)
                log_window.code("\n".join(rolling_logs))
                
            status.update(label="Mission Complete", state="complete", expanded=False)
        st.rerun()

with tab_vault:
    if not df_raw.empty:
        df = df_raw.copy()
        if hide_19: df = df[df['is_19'] == 0]
        if plus_only: df = df[df['is_plus'] == 1]
        df = df.sort_values("ratio", ascending=False)

        for _, row in df.iterrows():
            st.markdown(f"""
                <div class="gh-card">
                    <span class="ratio-badge">{row['ratio']} Ratio</span>
                    <a class="gh-title" href="{row['url']}">{row['title']}</a><br>
                    <small>by <b>{row['author']}</b> • {row['ep']} chapters • {row['fav']} favorites</small>
                    <div style="margin-top:10px;">
                        {" ".join([f'<span class="gh-tag">{t.strip()}</span>' for t in row['tags'].split(',')[:5]])}
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No novels in the vault. Run a Scout Mission first.")
