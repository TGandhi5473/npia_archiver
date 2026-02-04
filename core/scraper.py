import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9"
        }

    def _extract_from_meta(self, soup):
        """Extracts stats from the og:description tag using robust Regex."""
        meta = soup.find("meta", property="og:description")
        if not meta: return None, None, None
        
        content = meta.get("content", "")
        # This regex matches the keyword, optional colon/spaces, and the number with commas
        fav_m = re.search(r'선호\s*[:：]?\s*([\d,]+)', content)
        ep_m = re.search(r'회차\s*[:：]?\s*([\d,]+)', content)
        al_m = re.search(r'알람\s*[:：]?\s*([\d,]+)', content)

        def clean(m):
            return int(m.group(1).replace(',', '')) if m else 0

        return clean(fav_m), clean(ep_m), clean(al_m)

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id): return "SKIPPED"

        try:
            # follow_redirects=False prevents the 19+ login wall redirect
            with httpx.Client(headers=self.headers, follow_redirects=False) as client:
                resp = client.get(f"{self.base_url}{novel_id}", timeout=10.0)
                
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')
                fav, ep, al = self._extract_from_meta(soup)

                if not fav or not ep:
                    self.db.add_to_blacklist(novel_id, "GHOST")
                    return "BLACKLISTED (No Stats)"

                # Quality Gate (Adjust as needed)
                if fav < 30:
                    self.db.add_to_blacklist(novel_id, "LOW_FAV")
                    return f"REJECTED (Fav: {fav})"

                title_meta = soup.find("meta", property="og:title")
                title = title_meta.get("content", "Unknown").split(' - ')[0] if title_meta else "Unknown"

                data = {
                    'id': novel_id, 'title': title, 'author': "NPIA Scout",
                    'fav': fav, 'ep': ep, 'al': al,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': "R18" if "19세" in resp.text else "",
                    'is_19': 1 if "19세" in resp.text or resp.status_code == 302 else 0,
                    'is_plus': 1 if "plus" in resp.text.lower() else 0,
                    'url': f"{self.base_url}{novel_id}", 'date': datetime.now()
                }
                self.db.save_novel(data)
                return f"SUCCESS (Ratio: {data['ratio']})"
        except Exception as e:
            return f"ERR: {str(e)[:15]}"
