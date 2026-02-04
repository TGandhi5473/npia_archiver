import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import translate_tags, TAG_MAP

st.set_page_config(page_title="Sleeper Scout", layout="wide")
db = NovelDB(); scraper = NovelpiaScraper(db)

# Sidebar
with st.sidebar:
    st.header("🚀 Mass Recon")
    s_id = st.number_input("Start ID", value=383000)
    e_id = st.number_input("End ID", value=383020)
    if st.button("Start Scout"):
        p = st.progress(0)
        for i, nid in enumerate(range(int(s_id), int(e_id)+1)):
            scraper.scrape_novel(str(nid))
            p.progress((i+1)/(e_id-s_id+1))

# Tabs
t1, t2, t3 = st.tabs(["The Vault", "Market Share", "Surgical Scout"])

with t1:
    df = pd.read_sql("SELECT * FROM valid_novels", db.get_connection())
    if not df.empty:
        df['tags_en'] = df['tags'].apply(translate_tags)
        st.dataframe(df.sort_values("ratio", ascending=False), use_container_width=True)

with t2:
    stats = db.get_tag_stats()
    if stats:
        en_stats = {TAG_MAP.get(k, k): v for k, v in stats.items()}
        tag_df = pd.DataFrame(en_stats.items(), columns=['Tag', 'Count']).sort_values('Count', ascending=False)
        st.plotly_chart(px.pie(tag_df.head(12), values='Count', names='Tag', title="Top Genre Distribution", hole=0.3))

with t3:
    tid = st.text_input("Validation ID")
    if st.button("Run Recon"):
        st.json(scraper.scrape_novel(tid, return_raw=True))
