import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9"
        }

    def _safe_extract_number(self, soup, icon_alt):
        """
        Safely finds the number next to an icon with specific alt text.
        Prevents 'NoneType' errors by checking if the icon exists first.
        """
        icon = soup.find("img", alt=icon_alt)
        if not icon:
            return None
        
        # Look for the nearest text node containing numbers
        container = icon.find_next("span")
        if not container:
            return None
            
        text = container.get_text(strip=True).replace(',', '')
        nums = re.findall(r'\d+', text)
        return int(nums[0]) if nums else 0

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id):
            return "SKIPPED"

        url = f"{self.base_url}{novel_id}"
        try:
            response = httpx.get(url, headers=self.headers, timeout=15.0)
            if response.status_code != 200: return f"HTTP {response.status_code}"

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. GHOST DETECTION (The "Alarm" Word or Modal)
            # If the alert modal exists or 'deleted' text is found, kill it early.
            if soup.find(id="alert_modal") or "삭제된 소설" in response.text:
                self.db.add_to_blacklist(novel_id, "GHOST_ID")
                return "BLACKLISTED"

            # 2. DEFENSIVE STATS EXTRACTION
            # We use Korean labels from your screenshots: 선호 (Fav), 회차 (Ep), 알람 (Alarm)
            fav = self._safe_extract_number(soup, "선호")
            ep = self._safe_extract_number(soup, "회차")
            al = self._safe_extract_number(soup, "알람")

            # If any core stat is missing, the page structure is wrong (likely a ghost)
            if fav is None or ep is None:
                self.db.add_to_blacklist(novel_id, "STRUCTURE_MISMATCH")
                return "BLACKLISTED"

            # 3. DYNAMIC PIVOT LOGIC (350k)
            is_new = int(novel_id) > 350000
            limit = {'f': 25, 'e': 15, 'a': 10} if is_new else {'f': 150, 'e': 50, 'a': 80}

            if fav < limit['f'] or ep < limit['e'] or al < limit['a']:
                self.db.add_to_blacklist(novel_id, "LOW_STATS")
                return "BLACKLISTED"

            # 4. FINAL EXTRACTION
            title_el = soup.select_one(".title")
            author_el = soup.select_one(".author")
            
            if not title_el:
                self.db.add_to_blacklist(novel_id, "NO_TITLE")
                return "BLACKLISTED"

            tags = [t.get_text(strip=True).replace("#", "") for t in soup.select(".tag_item")]
            
            data = {
                'id': novel_id,
                'title': title_el.get_text(strip=True),
                'author': author_el.get_text(strip=True) if author_el else "Unknown",
                'fav': fav, 'ep': ep, 'al': al,
                'ratio': round(fav / ep, 2) if ep > 0 else 0,
                'tags': ", ".join(tags),
                'is_19': 1 if soup.select_one(".badge-19, .icon-19") else 0,
                'is_plus': 1 if soup.select_one(".badge-plus, .plus_icon") else 0,
                'url': url,
                'date': datetime.now()
            }

            self.db.save_novel(data)
            return "SUCCESS"

        except Exception as e:
            # Catch-all to ensure the loop never breaks
            return f"FAILED: {str(e)[:40]}"
