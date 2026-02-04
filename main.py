import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import translate_tags, TAG_MAP

# --- SETUP ---
st.set_page_config(page_title="Sleeper Scout 2026", layout="wide", page_icon="🎯")
db = NovelDB()
scraper = NovelpiaScraper(db)

# --- SIDEBAR: MISSION CONTROL ---
with st.sidebar:
    st.header("🎯 Mission Parameters")
    
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
                st.error("Security Wall Detected. Mission Aborted.")
                break
        st.success("Recon mission completed.")

    st.divider()
    
    st.subheader("Intelligence Filters")
    f_plus = st.checkbox("Plus Only", value=False)
    f_19 = st.checkbox("18+ Only", value=False)
    
    if st.button("🗑️ Purge Blacklist"):
        db.clear_blacklist()
        st.toast("Blacklist wiped.")

# --- MAIN UI TABS ---
st.title("🛡️ Sleeper Scout Dashboard")

tab_vault, tab_tags, tab_audit, tab_surgical = st.tabs([
    "📂 Intelligence Vault", 
    "📊 Market Share", 
    "📥 Translation Audit",
    "🔬 Surgical Entry"
])

# --- TAB 1: THE VAULT ---
with tab_vault:
    conn = db.get_connection()
    df = pd.read_sql("SELECT * FROM valid_novels", conn)
    
    if not df.empty:
        df['tags_en'] = df['tags'].apply(translate_tags)
        
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
                "tags_en": st.column_config.TextColumn("Translated Tags"),
                "last_updated": st.column_config.DatetimeColumn("Scouted At")
            },
            column_order=("novel_id", "title", "ratio", "fav", "ep", "al", "tags_en", "is_19", "is_plus", "url"),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("The vault is empty.")

# --- TAB 2: MARKET SHARE ---
with tab_tags:
    st.subheader("🏷️ Global Market Saturation")
    tag_counts = db.get_tag_stats()
    
    if tag_counts:
        # Group data for visualization
        translated_counts = {}
        for tag, count in tag_counts.items():
            en_tag = TAG_MAP.get(tag, f"[!] {tag}")
            translated_counts[en_tag] = translated_counts.get(en_tag, 0) + count
            
        tag_df = pd.DataFrame(translated_counts.items(), columns=['Tag', 'Frequency']).sort_values('Frequency', ascending=False)
        
        c1, c2 = st.columns([3, 2])
        with c1:
            top_n = 10
            chart_df = tag_df.head(top_n).copy()
            others_count = tag_df.iloc[top_n:]['Frequency'].sum()
            
            if others_count > 0:
                chart_df = pd.concat([chart_df, pd.DataFrame([{'Tag': 'Others', 'Frequency': others_count}])], ignore_index=True)

            fig = px.pie(chart_df, values='Frequency', names='Tag', hole=0.4, 
                         title=f"Top {top_n} Trope Distribution",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.write("### Trope Leaderboard")
            st.dataframe(tag_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No data found.")

# --- TAB 3: TRANSLATION AUDIT ---
with tab_audit:
    st.subheader("🔍 Missing Tag Mappings")
    tag_counts = db.get_tag_stats()
    
    if tag_counts:
        missing = {tag: count for tag, count in tag_counts.items() if tag not in TAG_MAP}
        
        if missing:
            m_df = pd.DataFrame(missing.items(), columns=['Korean Tag', 'Occurrences']).sort_values('Occurrences', ascending=False)
            
            st.warning(f"Found {len(m_df)} tags currently missing from your TAG_MAP.")
            
            col_l, col_r = st.columns(2)
            with col_l:
                st.write("### Frequency List")
                st.dataframe(m_df, use_container_width=True)
            with col_r:
                st.write("### Copy-Paste Generator")
                num_to_gen = st.slider("Tags to generate", 5, 50, 20)
                snippet = ",\n".join([f'    "{tag}": "??",' for tag in m_df['Korean Tag'].head(num_to_gen)])
                st.code(snippet, language='python')
        else:
            st.success("Perfect coverage! All tags in the database are accounted for in mappings.py.")
    else:
        st.info("No tags to audit yet.")

# --- TAB 4: SURGICAL ENTRY ---
with tab_surgical:
    st.subheader("Manual ID Recon")
    target_id = st.text_input("Target Novel ID")
    if st.button("Surgical Scout"):
        with st.spinner(f"Analyzing {target_id}..."):
            res = scraper.scrape_novel(target_id)
            st.code(res)
