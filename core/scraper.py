import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        # MIMIC A REAL BROWSER (CRITICAL FOR 2026 WAFS)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://novelpia.com/"
        }

    def _extract_stats_from_meta(self, soup):
        """
        Extracts stats from the og:description meta tag.
        Format: "조회: 124k | 추천: 5k | 선호: 5,092 | 회차: 120"
        """
        meta = soup.find("meta", property="og:description")
        if not meta:
            return None, None, None
            
        content = meta.get("content", "")
        
        # Regex to find numbers following specific Korean keywords
        # 선호 (Favorites), 회차 (Episodes), 알람 (Alarms)
        fav_match = re.search(r'선호\s*[:：]\s*([\d,]+)', content)
        ep_match = re.search(r'회차\s*[:：]\s*([\d,]+)', content)
        al_match = re.search(r'알람\s*[:：]\s*([\d,]+)', content)

        def clean_num(match):
            if not match: return 0
            return int(match.group(1).replace(',', ''))

        return clean_num(fav_match), clean_num(ep_match), clean_num(al_match)

    def scrape_novel(self, novel_id):
        # 1. EXISTENCE CHECK
        if self.db.check_exists(novel_id):
            return "SKIPPED (Already in Vault)"

        url = f"{self.base_url}{novel_id}"
        
        try:
            # 2. FETCH (NO REDIRECTS)
            # follow_redirects=False lets us see the meta tags on 19+ pages
            with httpx.Client(headers=self.headers, follow_redirects=False) as client:
                resp = client.get(url, timeout=10.0)
                
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404 Not Found")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')

                # 3. EXTRACT INTEL
                fav, ep, al = self._extract_stats_from_meta(soup)

                # 4. VALIDATION & QUALITY GATE
                if fav is None or ep is None:
                    self.db.add_to_blacklist(novel_id, "METADATA_MISSING")
                    return "BLACKLISTED (Invalid Layout)"

                # THE GATEKEEPER: Set your minimum quality bar here
                if fav < 50 or ep < 5:
                    self.db.add_to_blacklist(novel_id, f"LOW_STATS (Fav:{fav})")
                    return f"REJECTED (Low Stats: {fav} Favs)"

                # 5. DATA PREP
                title_meta = soup.find("meta", property="og:title")
                title = title_meta.get("content", "Unknown Title").split(' - ')[0] if title_meta else "Unknown"
                
                # Check for 19+ based on meta tags or redirect codes
                is_19 = 1 if (resp.status_code == 302 or "19세" in resp.text) else 0

                data = {
                    'id': novel_id,
                    'title': title,
                    'author': "NPIA Scout", # Author hidden in meta; body is restricted
                    'fav': fav,
                    'ep': ep,
                    'al': al or 0,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': "Restricted" if is_19 else "", 
                    'is_19': is_19,
                    'is_plus': 1 if "plus" in resp.text.lower() else 0,
                    'url': url,
                    'date': datetime.now()
                }

                self.db.save_novel(data)
                return f"SUCCESS (Ratio: {data['ratio']})"

        except Exception as e:
            return f"SYSTEM_ERROR: {str(e)[:30]}"
