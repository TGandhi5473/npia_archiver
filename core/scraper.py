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
            "Accept-Language": "ko-KR,ko;q=0.9",
            "Referer": "https://novelpia.com/"
        }

    def _extract_from_meta(self, soup):
        """
        Bypasses the 'Adult Gate' by pulling stats from OpenGraph meta tags.
        Example description: '조회: 1.2M | 추천: 45k | 선호: 3,500 | 회차: 125'
        """
        meta_desc = soup.find("meta", property="og:description")
        if not meta_desc:
            return None, None, None
        
        text = meta_desc.get("content", "")
        
        # Regex to find numbers after the Korean labels
        # 선호 (Favorites), 회차 (Episodes/Chapters), 알람 (Alarms)
        fav = re.search(r'선호\s*[:：]\s*([\d,]+)', text)
        ep = re.search(r'회차\s*[:：]\s*([\d,]+)', text)
        al = re.search(r'알람\s*[:：]\s*([\d,]+)', text)

        def clean(match):
            return int(match.group(1).replace(',', '')) if match else 0

        return clean(fav), clean(ep), clean(al)

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id):
            return "ALREADY_IN_VAULT"

        url = f"{self.base_url}{novel_id}"
        
        try:
            # VITAL: follow_redirects=False allows us to grab the meta tags 
            # from the landing page BEFORE it pushes us to the login screen.
            with httpx.Client(headers=self.headers, follow_redirects=False) as client:
                resp = client.get(url, timeout=10.0)
                
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404_NOT_FOUND")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')

                # 1. Try Meta Extraction (Works for 19+ and Standard)
                fav, ep, al = self._extract_from_meta(soup)

                # 2. Fallback to standard extraction if Meta failed
                if fav is None or ep is None:
                    # (Standard extraction logic here if needed)
                    self.db.add_to_blacklist(novel_id, "GHOST_OR_INVALID")
                    return "BLACKLISTED (GHOST)"

                # 3. Quality Check (The 'Bad Novel' Filter)
                # This ensures your DB only stays clean with novels worth scouting
                if fav < 50 or ep < 5:
                    self.db.add_to_blacklist(novel_id, "LOW_SIGNAL")
                    return f"REJECTED (Fav: {fav}, Ep: {ep})"

                # 4. Success Data Preparation
                title = soup.find("meta", property="og:title")
                title_text = title.get("content", "Unknown").split(' - ')[0] if title else "Unknown"
                
                # Fetch cover image from meta (bypass adult blur)
                cover_meta = soup.find("meta", property="og:image")
                cover_url = cover_meta.get("content", "") if cover_meta else ""

                data = {
                    'id': novel_id,
                    'title': title_text,
                    'author': "NPIA Explorer", # Author is rarely in meta, found in body
                    'fav': fav,
                    'ep': ep,
                    'al': al or 0,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': "", # Tags are in body; hard to get if age-gated
                    'is_19': 1 if "19세" in resp.text or "mature" in url else 0,
                    'is_plus': 1 if "plus" in resp.text else 0,
                    'url': url,
                    'cover': cover_url,
                    'date': datetime.now()
                }

                self.db.save_novel(data)
                return f"SUCCESS (Ratio: {data['ratio']})"

        except Exception as e:
            return f"FAILED: {str(e)[:30]}"
