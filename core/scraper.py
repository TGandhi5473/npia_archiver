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

    def _extract_number(self, element):
        """Dives into nested font tags to find the raw number."""
        if not element: return 0
        # Finds the deepest text (e.g., '14,991')
        text = element.get_text(strip=True)
        nums = re.findall(r'\d+', text.replace(',', ''))
        return int(nums[0]) if nums else 0

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id):
            return "SKIPPED"

        url = f"{self.base_url}{novel_id}"
        try:
            response = httpx.get(url, headers=self.headers, timeout=15.0)
            if response.status_code != 200: return "ERROR"

            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. GHOST DETECTION (Matching image_fca4e6.png & image_fd2485.png)
            # Check for the alert modal or the 'deleted novel' message
            is_deleted = soup.find(id="alert_modal") or "삭제된 소설" in response.text
            if is_deleted:
                self.db.add_to_blacklist(novel_id, "MISSING")
                return "BLACKLISTED"

            # 2. STATS EXTRACTION (Matching image_fc3f27.png nested font structure)
            # Preference is in .info-count2; Episodes and Alarms follow similar patterns
            info_box = soup.select_one(".info-graybox")
            if not info_box:
                return "ERROR: Structure Mismatch"

            # Select based on the icon alt text 'Preference' or specific spans
            fav = self._extract_number(soup.find("img", alt="Preference").find_next("span", class_="writer-name"))
            # Note: You can replicate the find logic for 'Episode' and 'Alarm' icons
            ep = self._extract_number(soup.find(string=re.compile("회차"))) 
            al = self._extract_number(soup.find(string=re.compile("알람")))

            # 3. DYNAMIC THRESHOLD (The 350k Pivot)
            pivot_id = 350000
            limit = {'f': 25, 'e': 15, 'a': 10} if int(novel_id) > pivot_id else {'f': 150, 'e': 50, 'a': 80}

            if fav < limit['f'] or ep < limit['e'] or al < limit['a']:
                self.db.add_to_blacklist(novel_id, "BELOW_THRESHOLD")
                return "BLACKLISTED"

            # 4. TAG EXTRACTION (Matching image_fc2849.png)
            # Dive 2 layers within the span class="tag"
            tag_spans = soup.select(".writer-tag span.tag")
            tags = [t.get_text(strip=True).replace("#", "") for t in tag_spans]

            # 5. FINAL SUCCESS DATA
            data = {
                'id': novel_id,
                'title': soup.select_one(".title").get_text(strip=True),
                'author': soup.select_one(".author").get_text(strip=True) if soup.select_one(".author") else "Unknown",
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
            return f"FAILED: {str(e)[:50]}"
