import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def _extract_all(self, soup, text):
        """Extracts cleaned Title, Author, Stats, and Tags."""
        
        # 1. Meta Logic (Title & Author)
        # Using attrs to avoid the 'name' argument conflict
        t_meta = soup.find("meta", property="og:title")
        title = t_meta["content"].split(" : ")[0].strip() if t_meta else "Unknown Title"
        
        a_meta = soup.find("meta", property="og:author") or soup.find("meta", attrs={"name": "author"})
        author = a_meta["content"] if a_meta else "Unknown Author"

        # 2. Stats Logic (Views, Recs, Favs, Episodes)
        def get_stat(patterns):
            for pat in patterns:
                match = re.search(pat, text)
                if match:
                    val = match.group(1).replace(',', '')
                    # Handle Korean '만' (10,000) unit
                    if '만' in val:
                        return int(float(val.replace('만', '')) * 10000)
                    return int(val)
            return 0

        fav = get_stat([r'선호\s*[:：]?\s*([\d,]+)'])
        ep = get_stat([r'회차\s*[:：]?\s*([\d,]+)'])
        views = get_stat([r'조회\s*[:：]?\s*([\d,.]+[만]?)'])
        recs = get_stat([r'추천\s*[:：]?\s*([\d,]+)'])

        # 3. Clean Tag Logic (Filtering out CSS/JS noise)
        # We target the 'novel_info' div to avoid site-wide CSS IDs
        tag_area = soup.find("div", class_="novel_info") or soup
        raw_tags = re.findall(r'#([가-힣a-zA-Z0-9]{2,20})', tag_area.get_text())
        
        # Filter: Exclude hex codes, technical terms, and UI elements
        tech_noise = {'ffffff', 'dddddd', 'tab', 'load', 'ddd', 'fff', 'btn', 'plus'}
        clean_tags = [
            t for t in raw_tags 
            if t.lower() not in tech_noise 
            and not re.match(r'^[a-fA-F0-9]{6}$', t) # Filters hex codes like a824ff
            and not any(x in t for x in ['Wrapper', 'Btn', 'Box', 'sideTicket', 'modal'])
        ]
        
        tags_str = ",".join(list(set(clean_tags)))

        return {
            "title": title, "author": author,
            "fav": fav, "ep": ep, "views": views, "recs": recs,
            "tags": tags_str,
            "is_19": 1 if "19세" in text else 0,
            "is_plus": 1 if "플러스" in text or "plus" in text.lower() else 0
        }

    def scrape_novel(self, nid, return_raw=False):
        """Scrapes a single novel ID and saves to DB unless return_raw is True."""
        if not return_raw and self.db.check_exists(nid):
            return "SKIPPED"
            
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(f"{self.base_url}{nid}", timeout=10.0)
                
                if resp.status_code == 404:
                    if not return_raw: self.db.add_to_blacklist(nid, "404")
                    return "404"
                
                soup = BeautifulSoup(resp.text, 'lxml')
                data = self._extract_all(soup, resp.text)
                
                # Metadata for the database
                data.update({
                    'id': nid,
                    'url': f"{self.base_url}{nid}",
                    'date': datetime.now(),
                    'ratio': round(data['fav'] / data['ep'], 2) if data['ep'] > 0 else 0
                })

                if not return_raw:
                    self.db.save_novel(data)
                
                return data
        except Exception as e:
            return {"error": str(e)}
