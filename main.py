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

# --- SIDEBAR: SCOUTING COMMAND ---
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
    st.subheader("Global Filters")
    f_plus = st.checkbox("Plus Only", value=False)
    f_19 = st.checkbox("18+ Only (NSFW)", value=False)
    
    if st.button("🗑️ Purge Blacklist"):
        db.clear_blacklist()
        st.toast("Blacklist wiped.")

# --- TABS ---
tab_vault, tab_market, tab_associations, tab_audit = st.tabs([
    "📂 Intelligence Vault", "📊 Market Share", "🔗 Trope Associations", "🔍 Translation Audit"
])

# --- TAB 1: INTELLIGENCE VAULT ---
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
            column_config={
                "url": st.column_config.LinkColumn("Access"), 
                "ratio": st.column_config.NumberColumn("Ratio", format="%.2f ⭐")
            },
            column_order=("novel_id", "title", "ratio", "fav", "ep", "tags_en", "is_19", "is_plus", "url"),
            use_container_width=True, hide_index=True
        )

# --- TAB 2: MARKET SHARE (OVERALL) ---
with tab_market:
    tag_counts = db.get_tag_stats()
    if tag_counts:
        # Translate keys using TAG_MAP
        translated = {TAG_MAP.get(k, f"[Unmapped] {k}"): v for k, v in tag_counts.items()}
        tag_df = pd.DataFrame(translated.items(), columns=['Tag', 'Frequency']).sort_values('Frequency', ascending=False)
        
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = px.pie(tag_df.head(15), values='Frequency', names='Tag', hole=0.4, 
                         title="Top 15 Market Tropes (Global)")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.subheader("Raw Distribution")
            st.dataframe(tag_df, use_container_width=True, hide_index=True)

# --- TAB 3: TROPE ASSOCIATIONS (NEW PIE CHARTS) ---
with tab_associations:
    st.header("🔗 Major Genre Deep-Dive")
    st.write("Understand the 'Sub-tags' most commonly found within major genres.")
    
    # Define English keys for the user to pick from
    major_genres_en = ["Fantasy", "Harem", "Romance", "Modern Fantasy", "Martial Arts", "Academy", "Streaming", "Gender Bender"]
    # Reverse mapping to find Korean tags in the DB
    EN_TO_KO = {v: k for k, v in TAG_MAP.items()}
    
    selected_genre_en = st.selectbox("Select Genre to Analyze", major_genres_en)
    selected_genre_ko = EN_TO_KO.get(selected_genre_en)
    
    if selected_genre_ko:
        # Logic: Find novels that have the selected genre and count their OTHER tags
        # We query the DB for any novel containing the Korean anchor tag
        query = f"SELECT tags FROM valid_novels WHERE tags LIKE '%{selected_genre_ko}%'"
        novels_with_tag = pd.read_sql(query, db.get_connection())
        
        if not novels_with_tag.empty:
            all_associated_tags = []
            for tag_str in novels_with_tag['tags']:
                tags = [t.strip() for t in tag_str.split(',') if t.strip() != selected_genre_ko]
                all_associated_tags.extend(tags)
            
            assoc_counts = pd.Series(all_associated_tags).value_counts().head(10)
            assoc_df = pd.DataFrame({'Tag_KO': assoc_counts.index, 'Count': assoc_counts.values})
            assoc_df['Tag_EN'] = assoc_df['Tag_KO'].apply(lambda x: TAG_MAP.get(x, x))
            
            fig_assoc = px.pie(assoc_df, values='Count', names='Tag_EN', hole=0.5,
                               title=f"Sub-Tropes often found with {selected_genre_en}")
            st.plotly_chart(fig_assoc, use_container_width=True)
        else:
            st.info(f"Not enough data in the vault for {selected_genre_en} yet.")

# --- TAB 4: TRANSLATION AUDIT ---
with tab_audit:
    st.subheader("🔍 Missing Mappings")
    tag_counts = db.get_tag_stats()
    if tag_counts:
        missing = [{"Korean": k, "Frequency": v} for k, v in tag_counts.items() if k not in TAG_MAP]
        if missing:
            st.warning(f"Found {len(missing)} unmapped Korean tags.")
            st.dataframe(pd.DataFrame(missing).sort_values("Frequency", ascending=False), use_container_width=True)
        else:
            st.success("Translation Dictionary is 100% complete!")
