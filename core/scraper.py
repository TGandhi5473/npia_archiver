import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }

    def _extract_data_points(self, soup):
        """
        Targeting the text directly since metadata is stripped.
        Searches for: 선호 (Favorites), 회차 (Chapters), 알람 (Alarms)
        """
        full_text = soup.get_text()
        
        # Regex to find numbers immediately following the keywords
        # Supports formats like '선호5,092' or '선호 : 5,092'
        fav_match = re.search(r'선호\s*[:：]?\s*([\d,]+)', full_text)
        ep_match = re.search(r'회차\s*[:：]?\s*([\d,]+)', full_text)
        
        def clean_to_int(match):
            if not match: return 0
            # Remove commas and convert to integer
            return int(match.group(1).replace(',', ''))

        return clean_to_int(fav_match), clean_to_int(ep_match)

    def scrape_novel(self, novel_id):
        url = f"{self.base_url}{novel_id}"
        try:
            # For 19+ content, follow_redirects=True is needed to reach the warning page
            # which usually contains the stats even if the content is blurred.
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url, timeout=10.0)
                soup = BeautifulSoup(resp.text, 'lxml')
                
                fav, ep = self._extract_data_points(soup)

                # Validation
                if fav == 0 and ep == 0:
                    return f"FAILED: Data not found in body for {novel_id}"

                ratio = round(fav / ep, 2) if ep > 0 else 0
                
                # We also need the tags (plus, 19, etc.)
                is_19 = 1 if "19세" in resp.text else 0
                is_plus = 1 if "플러스" in resp.text or "plus" in resp.text.lower() else 0

                # Data for DB
                data = {
                    'id': novel_id,
                    'title': self._get_clean_title(soup),
                    'author': "NPIA Scout",
                    'fav': fav,
                    'ep': ep,
                    'al': 0,
                    'ratio': ratio,
                    'tags': "R18" if is_19 else "General",
                    'is_19': is_19,
                    'is_plus': is_plus,
                    'url': url,
                    'date': datetime.now()
                }
                self.db.save_novel(data)
                return f"SUCCESS (Ratio: {ratio} | Fav: {fav} | Ep: {ep})"
        except Exception as e:
            return f"ERR: {str(e)[:25]}"

    def _get_clean_title(self, soup):
        title_meta = soup.find("meta", property="og:title")
        if title_meta:
            return title_meta.get("content", "Unknown").replace("노벨피아 - ", "").split(" - ")[0]
        return "Unknown"
