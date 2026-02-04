import streamlit as st
import pandas as pd
import plotly.express as px
from core.database import NovelDB
from core.scraper import NovelpiaScraper
from core.mappings import translate_tags, TAG_MAP

st.set_page_config(page_title="Sleeper Scout", layout="wide")
db = NovelDB(); scraper = NovelpiaScraper(db)

with st.sidebar:
    st.header("🎯 Mass Scout")
    s_id = st.number_input("Start ID", value=383000)
    e_id = st.number_input("End ID", value=383010)
    if st.button("🚀 Start Recon"):
        bar = st.progress(0)
        for i, nid in enumerate(range(int(s_id), int(e_id)+1)):
            scraper.scrape_novel(str(nid))
            bar.progress((i+1)/(e_id-s_id+1))

t1, t2, t3 = st.tabs(["Vault", "Tag Analytics", "Surgical Scout"])

with t1:
    df = pd.read_sql("SELECT * FROM valid_novels", db.get_connection())
    if not df.empty:
        df['tags_en'] = df['tags'].apply(translate_tags)
        st.dataframe(df.sort_values("ratio", ascending=False), use_container_width=True)

with t2:
    stats = db.get_tag_stats()
    if stats:
        en_stats = {TAG_MAP.get(k, k): v for k, v in stats.items()}
        tag_df = pd.DataFrame(en_stats.items(), columns=['Genre', 'Hits']).sort_values('Hits', ascending=False)
        st.plotly_chart(px.pie(tag_df.head(10), values='Hits', names='Genre', hole=0.4))

with t3:
    tid = st.text_input("Enter Novel ID to Verify")
    if st.button("Analyze HTML Structure"):
        st.json(scraper.scrape_novel(tid, return_raw=True))
