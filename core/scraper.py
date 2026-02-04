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
            "Accept-Language": "ko-KR,ko;q=0.9"
        }

    def _extract_from_meta(self, soup):
        meta_desc = soup.find("meta", property="og:description")
        if not meta_desc: return None, None, None
        
        text = meta_desc.get("content", "")
        fav = re.search(r'선호\s*[:：]\s*([\d,]+)', text)
        ep = re.search(r'회차\s*[:：]\s*([\d,]+)', text)
        al = re.search(r'알람\s*[:：]\s*([\d,]+)', text)

        def clean(match):
            return int(match.group(1).replace(',', '')) if match else 0
        return clean(fav), clean(ep), clean(al)

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id): return "EXISTS"

        try:
            # follow_redirects=False is the key to seeing 19+ stats without an account
            with httpx.Client(headers=self.headers, follow_redirects=False) as client:
                resp = client.get(f"{self.base_url}{novel_id}", timeout=10.0)
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')
                fav, ep, al = self._extract_from_meta(soup)

                if fav is None or ep is None:
                    self.db.add_to_blacklist(novel_id, "GHOST")
                    return "BLACKLISTED (GHOST)"

                # Quality Gate: Keeps the "bad" novels out of your Vault
                if fav < 50 or ep < 5:
                    self.db.add_to_blacklist(novel_id, "LOW_STATS")
                    return f"REJECTED (Fav: {fav})"

                title_meta = soup.find("meta", property="og:title")
                title = title_meta.get("content", "Unknown").split(' - ')[0] if title_meta else "Unknown"

                data = {
                    'id': novel_id, 'title': title, 'author': "NPIA Scout",
                    'fav': fav, 'ep': ep, 'al': al,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': "", 'is_19': 1 if "19세" in resp.text else 0,
                    'is_plus': 1 if "plus" in resp.text else 0,
                    'url': f"{self.base_url}{novel_id}", 'date': datetime.now()
                }
                self.db.save_novel(data)
                return f"SUCCESS (Ratio: {data['ratio']})"
        except Exception as e:
            return f"ERR: {str(e)[:20]}"
