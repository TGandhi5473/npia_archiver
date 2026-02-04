import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"

    def _extract_all(self, soup, text):
        # FIX: Using attrs={"name": "author"} to avoid the BeautifulSoup 'name' conflict
        t_meta = soup.find("meta", property="og:title")
        title = t_meta["content"].split(" : ")[0].strip() if t_meta else "Unknown"
        
        a_meta = soup.find("meta", property="og:author") or soup.find("meta", attrs={"name": "author"})
        author = a_meta["content"] if a_meta else "Unknown"

        def get_stat(pat):
            m = re.search(pat, text)
            if not m: return 0
            val = m.group(1).replace(',', '')
            if '만' in val: return int(float(val.replace('만', '')) * 10000)
            return int(val)

        fav = get_stat(r'선호\s*[:：]?\s*([\d,]+)')
        ep = get_stat(r'회차\s*[:：]?\s*([\d,]+)')
        views = get_stat(r'조회\s*[:：]?\s*([\d,.]+[만]?)')
        recs = get_stat(r'추천\s*[:：]?\s*([\d,]+)')
        tags = ",".join(list(set(re.findall(r'#([가-힣a-zA-Z0-9]+)', text))))

        return {
            "title": title, "author": author, "fav": fav, "ep": ep,
            "views": views, "recs": recs, "tags": tags,
            "is_19": 1 if "19세" in text else 0,
            "is_plus": 1 if "플러스" in text or "plus" in text.lower() else 0
        }

    def scrape_novel(self, nid, return_raw=False):
        try:
            with httpx.Client(follow_redirects=True) as client:
                resp = client.get(f"{self.base_url}{nid}", timeout=10.0)
                soup = BeautifulSoup(resp.text, 'lxml')
                data = self._extract_all(soup, resp.text)
                data.update({'id': nid, 'url': f"{self.base_url}{nid}", 'date': datetime.now()})
                data['ratio'] = round(data['fav'] / data['ep'], 2) if data['ep'] > 0 else 0
                
                if not return_raw: self.db.save_novel(data)
                return data
        except Exception as e: return {"error": str(e)}
