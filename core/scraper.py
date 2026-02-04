import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        
        # Dead giveaway tags for 18+ classification based on your focus
        self.ADULT_RED_FLAGS = [
            "ntl", "ntr", "고수위", "조교", "능욕", "최면", 
            "관음", "역강간", "촉수", "근친", "절륜", "성인"
        ]
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }

    def _extract_stats_and_tags(self, soup):
        full_text = soup.get_text()
        
        fav_m = re.search(r'선호\s*[:：]?\s*([\d,]+)', full_text)
        ep_m = re.search(r'회차\s*[:：]?\s*([\d,]+)', full_text)
        al_m = re.search(r'알람\s*[:：]?\s*([\d,]+)', full_text)
        
        def clean(m):
            return int(m.group(1).replace(',', '')) if m else 0

        tags_found = re.findall(r'#([가-힣a-zA-Z0-9]+)', full_text)
        tags_str = ",".join(list(set(tags_found)))

        return clean(fav_m), clean(ep_m), clean(al_m), tags_str

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id):
            return "SKIPPED (Existing)"

        url = f"{self.base_url}{novel_id}"
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url, timeout=10.0)
                
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')
                fav, ep, al, tags = self._extract_stats_and_tags(soup)

                if fav < 10 or ep < 1:
                    self.db.add_to_blacklist(novel_id, "LOW_SIGNAL")
                    return "BLACKLISTED (Insufficient Data)"

                # --- 18+ LOGIC OVERRIDE ---
                is_18 = 1 if "19세" in resp.text else 0
                
                # Check tags for adult content (case-insensitive for ntl/ntr)
                tag_list = [t.lower() for t in tags.split(',')]
                if any(flag in tag_list for flag in self.ADULT_RED_FLAGS):
                    is_18 = 1
                # --------------------------

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
                    'is_19': is_18,
                    'is_plus': 1 if "플러스" in resp.text or "plus" in resp.text.lower() else 0,
                    'url': url,
                    'date': datetime.now()
                }

                self.db.save_novel(data)
                return f"SUCCESS (18+: {'YES' if is_18 else 'NO'} | Ratio: {data['ratio']})"

        except Exception as e:
            return f"ERR: {str(e)[:20]}"
