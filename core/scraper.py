import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        self.api_url = "https://novelpia.com/proc/novel_curation?cmd=epi_list_curation&main_genre=1&novel_no="
        
        # Standard headers to look like a normal browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-Requested-With": "XMLHttpRequest"
        }

    def _extract_meta(self, soup, text):
        """Extracts Title, Author, and Tags from public HTML meta tags."""
        # 1. Title & Author
        t_meta = soup.find("meta", property="og:title")
        title = t_meta["content"].split(" : ")[0].strip() if t_meta else "Unknown"
        
        a_meta = soup.find("meta", property="og:author") or soup.find("meta", attrs={"name": "author"})
        author = a_meta["content"] if a_meta else "Unknown"

        # 2. Targeted Tag Cleaning (Ignores CSS/JS noise)
        tag_area = soup.find("div", class_="novel_info") or soup
        raw_tags = re.findall(r'#([가-힣a-zA-Z0-9]{2,20})', tag_area.get_text())
        
        noise = {'ffffff', 'dddddd', 'tab', 'load', 'ddd', 'fff', 'btn', 'plus', 'is'}
        clean_tags = [t for t in raw_tags if t.lower() not in noise and not re.match(r'^[a-fA-F0-9]{6}$', t)]
        tags_str = ",".join(list(set(clean_tags)))

        # 3. Maturity & Plus Status
        is_18 = 1 if ("19세" in text or any(x in tags_str for x in ["고수위", "19금", "NTL"])) else 0
        is_plus = 1 if ("플러스" in text or "plus" in text.lower()) else 0

        return {
            "title": title, "author": author, "tags": tags_str,
            "is_19": is_18, "is_plus": is_plus
        }

    def _fetch_api_stats(self, nid):
        """Attempts to fetch raw stats from the API as a guest."""
        try:
            with httpx.Client(headers=self.headers) as client:
                resp = client.get(f"{self.api_url}{nid}", timeout=10.0)
                if resp.status_code != 200:
                    return {"views": 0, "fav": 0, "recs": 0, "ep": 0}
                
                data = resp.json()
                return {
                    "views": int(data.get("view_cnt", 0)),
                    "fav": int(data.get("favor_cnt", 0)),
                    "recs": int(data.get("good_cnt", 0)),
                    "ep": int(data.get("epi_cnt", 0)) or len(data.get("epi_list", []))
                }
        except:
            return {"views": 0, "fav": 0, "recs": 0, "ep": 0}

    def scrape_novel(self, nid, return_raw=False):
        """Main scout function."""
        if not return_raw and self.db.check_exists(nid):
            return "SKIPPED"
            
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                # Step 1: Get Metadata
                html_resp = client.get(f"{self.base_url}{nid}", timeout=10.0)
                if html_resp.status_code == 404:
                    if not return_raw: self.db.add_to_blacklist(nid, "404")
                    return "404"
                
                soup = BeautifulSoup(html_resp.text, 'lxml')
                meta_data = self._extract_meta(soup, html_resp.text)
                
                # Step 2: Get Stats
                stats = self._fetch_api_stats(nid)
                
                # Step 3: Combine and calculate Ratio
                final_data = {**meta_data, **stats, "id": nid, "url": f"{self.base_url}{nid}", "date": datetime.now()}
                
                # Calculate Sleeper Ratio (Favs per Episode)
                final_data['ratio'] = round(final_data['fav'] / final_data['ep'], 2) if final_data.get('ep', 0) > 0 else 0
                
                if not return_raw:
                    self.db.save_novel(final_data)
                
                return final_data
        except Exception as e:
            return {"error": str(e)}
