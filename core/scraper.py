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

    def _extract_stats_and_tags(self, soup):
        """Deep searches the body text for stats and hashtags."""
        full_text = soup.get_text()
        
        # 1. Extract Stats (using numeric regex)
        fav_m = re.search(r'선호\s*[:：]?\s*([\d,]+)', full_text)
        ep_m = re.search(r'회차\s*[:：]?\s*([\d,]+)', full_text)
        al_m = re.search(r'알람\s*[:：]?\s*([\d,]+)', full_text)
        
        def clean(m):
            return int(m.group(1).replace(',', '')) if m else 0

        # 2. Extract All Tags (#TagFormat)
        # Finds words starting with # followed by Korean/Alphanumeric
        tags_found = re.findall(r'#([가-힣a-zA-Z0-9]+)', full_text)
        tags_str = ",".join(list(set(tags_found))) # Unique tags only

        return clean(fav_m), clean(ep_m), clean(al_m), tags_str

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id):
            return "SKIPPED (Existing)"

        url = f"{self.base_url}{novel_id}"
        try:
            # follow_redirects=True ensures we hit the blurred adult page if redirected
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url, timeout=10.0)
                
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')
                fav, ep, al, tags = self._extract_stats_and_tags(soup)

                # Quality Control: Filter out 'Ghost' novels
                if fav < 10 or ep < 1:
                    self.db.add_to_blacklist(novel_id, "LOW_SIGNAL")
                    return "BLACKLISTED (Insufficient Data)"

                # Metadata for Title
                title_meta = soup.find("meta", property="og:title")
                title = title_meta.get("content", "Unknown").replace("노벨피아 - ", "").split(" - ")[0] if title_meta else f"Novel_{novel_id}"

                data = {
                    'id': novel_id,
                    'title': title,
                    'author': "NPIA Scout",
                    'fav': fav,
                    'ep': ep,
                    'al': al,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': tags,
                    'is_19': 1 if "19세" in resp.text else 0,
                    'is_plus': 1 if "플러스" in resp.text or "plus" in resp.text.lower() else 0,
                    'url': url,
                    'date': datetime.now()
                }

                self.db.save_novel(data)
                return f"SUCCESS (Ratio: {data['ratio']} | Tags: {len(tags.split(',')) if tags else 0})"

        except Exception as e:
            return f"ERR: {str(e)[:20]}"
