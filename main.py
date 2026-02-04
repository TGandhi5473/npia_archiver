import streamlit as st
import pandas as pd
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import translate_tags, TAG_MAP
import plotly.express as px

st.set_page_config(page_title="Scouting Hits", layout="wide")
db = NovelDB(); scraper = NovelpiaScraper(db)

# Sidebar
with st.sidebar:
    st.header("🎯 Scout Settings")
    s_id = st.number_input("Start", value=383000)
    e_id = st.number_input("End", value=383100)
    if st.button("🚀 Mass Scout"):
        p = st.progress(0)
        for i, nid in enumerate(range(int(s_id), int(e_id)+1)):
            scraper.scrape_novel(str(nid))
            p.progress((i+1)/(e_id-s_id+1))
    st.divider()
    f_plus = st.checkbox("Plus Only")
    f_19 = st.checkbox("18+ Only")

# Main Tabs
t1, t2, t3 = st.tabs(["Vault", "Tag Analytics", "Surgical Scout"])

with t1:
    df = pd.read_sql("SELECT * FROM valid_novels", db.get_connection())
    if not df.empty:
        if f_plus: df = df[df['is_plus'] == 1]
        if f_19: df = df[df['is_19'] == 1]
        df['tags_en'] = df['tags'].apply(translate_tags)
        st.dataframe(df.sort_values("ratio", ascending=False), use_container_width=True, hide_index=True)

with t2:
    stats = db.get_tag_stats()
    if stats:
        en_stats = {TAG_MAP.get(k, k): v for k, v in stats.items()}
        tag_df = pd.DataFrame(en_stats.items(), columns=['Genre', 'Hits']).sort_values('Hits', ascending=False)
        st.plotly_chart(px.pie(tag_df.head(10), values='Hits', names='Genre', hole=0.4))
        st.dataframe(tag_df, use_container_width=True)

with t3:
    tid = st.text_input("Validation ID")
    if st.button("Run Surgical Scout"):
        res = scraper.scrape_novel(tid, return_raw=True)
        st.write(res)
