import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import translate_tags, TAG_MAP
from deep_translator import GoogleTranslator

# --- SETUP ---
st.set_page_config(page_title="Sleeper Scout 2026", layout="wide", page_icon="🎯")
db = NovelDB()
scraper = NovelpiaScraper(db)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Mission Parameters")
    col_s, col_e = st.columns(2)
    start_id = col_s.number_input("Start ID", value=383000)
    end_id = col_e.number_input("End ID", value=383100)
    
    if st.button("🚀 Launch Scout Mission", use_container_width=True):
        progress_bar = st.progress(0)
        total_tasks = int(end_id - start_id + 1)
        for i, nid in enumerate(range(int(start_id), int(end_id) + 1)):
            scraper.scrape_novel(str(nid))
            progress_bar.progress((i + 1) / total_tasks)
        st.success("Mission completed.")

    st.divider()
    f_plus = st.checkbox("Plus Only", value=False)
    f_19 = st.checkbox("18+ Only", value=False)
    if st.button("🗑️ Purge Blacklist"):
        db.clear_blacklist()
        st.toast("Blacklist wiped.")

# --- TABS ---
tab_vault, tab_tags, tab_audit, tab_surgical = st.tabs([
    "📂 Intelligence Vault", "📊 Market Share", "📥 Translation Audit", "🔬 Surgical Entry"
])

# --- TAB 1: VAULT ---
with tab_vault:
    df = pd.read_sql("SELECT * FROM valid_novels", db.get_connection())
    if not df.empty:
        df['tags_en'] = df['tags'].apply(translate_tags)
        if f_plus: df = df[df['is_plus'] == 1]
        if f_19: df = df[df['is_19'] == 1]

        def highlight_18(row):
            return ['background-color: rgba(255, 75, 75, 0.15)'] * len(row) if row.is_19 == 1 else [''] * len(row)

        st.dataframe(
            df.sort_values(by="ratio", ascending=False).style.apply(highlight_18, axis=1),
            column_config={"url": st.column_config.LinkColumn("Access"), "ratio": st.column_config.NumberColumn("Ratio", format="%.2f ⭐")},
            column_order=("novel_id", "title", "ratio", "fav", "ep", "tags_en", "is_19", "is_plus", "url"),
            use_container_width=True, hide_index=True
        )

# --- TAB 2: MARKET SHARE ---
with tab_tags:
    tag_counts = db.get_tag_stats()
    if tag_counts:
        translated = {TAG_MAP.get(k, f"[!] {k}"): v for k, v in tag_counts.items()}
        tag_df = pd.DataFrame(translated.items(), columns=['Tag', 'Freq']).sort_values('Freq', ascending=False)
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = px.pie(tag_df.head(10), values='Freq', names='Tag', hole=0.4, title="Top 10 Tropes")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.dataframe(tag_df, use_container_width=True, hide_index=True)

# --- TAB 3: TRANSLATION AUDIT (AUTOMATED) ---
with tab_audit:
    st.subheader("🔍 Automatic Trope Mapping")
    tag_counts = db.get_tag_stats()
    
    if tag_counts:
        missing_tags = [k for k in tag_counts.keys() if k not in TAG_MAP]
        
        if missing_tags:
            st.warning(f"Detected {len(missing_tags)} tags missing English translations.")
            
            if st.button("🪄 Magic Translate (Auto-suggest English)"):
                with st.spinner("Translating tropes..."):
                    translator = GoogleTranslator(source='ko', target='en')
                    # Batch processing to prevent timeout
                    suggestions = {}
                    for tag in missing_tags:
                        try:
                            # Handle common slang/tropes manually if needed, otherwise use Google
                            suggestions[tag] = translator.translate(tag)
                        except:
                            suggestions[tag] = "Translation Error"
                    
                    # Create the code block for mappings.py
                    code_lines = [f'    "{k}": "{v}",' for k, v in suggestions.items()]
                    st.success("Translations generated! Copy the block below into your TAG_MAP:")
                    st.code("\n".join(code_lines), language='python')
            
            # Simple list view
            m_df = pd.DataFrame([{"Korean": k, "Count": tag_counts[k]} for k in missing_tags]).sort_values("Count", ascending=False)
            st.dataframe(m_df, use_container_width=True)
        else:
            st.success("All tags are currently translated in mappings.py!")
    else:
        st.info("No data available to audit.")

# --- TAB 4: SURGICAL ENTRY ---
with tab_surgical:
    target_id = st.text_input("Target Novel ID")
    if st.button("Surgical Scout"):
        st.code(scraper.scrape_novel(target_id))
