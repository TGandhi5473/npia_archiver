# ==========================================
# FILE: core/scraper.py
# ==========================================
import cloudscraper
from bs4 import BeautifulSoup
import re
import time
from .database import NovelDB
from .filters import is_high_quality

class NovelArchiver:
    def __init__(self):
        self.db = NovelDB()
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        self.base_url = "https://novelpia.com/novel/"

    def clean_numeric(self, value):
        if not value: return 0
        text = str(value).replace(',', '').strip()
        if '만' in text:
            try: return int(float(text.replace('만', '')) * 10000)
            except: return 0
        digits = re.sub(r'[^0-9]', '', text)
        return int(digits) if digits else 0

    def scrape_novel(self, novel_id):
        if self.db.is_cached(novel_id):
            return "Cached"

        url = f"{self.base_url}{novel_id}"
        try:
            response = self.scraper.get(url, timeout=10)
            
            # 1. Handle HTTP errors (Removed/Private)
            if response.status_code == 404:
                return "Parse Error: Novel Removed"
            if response.status_code == 403:
                return "Parse Error: Private/Restricted"

            soup = BeautifulSoup(response.text, 'html.parser')

            # 2. Handle Logic Errors (Missing Elements)
            title_tag = soup.select_one(".title")
            if not title_tag or "존재하지 않는" in response.text:
                return "Parse Error: Novel Removed"

            # 3. Extract Metadata
            metadata = {
                "title": title_tag.get_text(strip=True),
                "writer": soup.select_one(".writer").get_text(strip=True) if soup.select_one(".writer") else "Unknown",
                "views": self.clean_numeric(soup.select_one(".view_count").text if soup.select_one(".view_count") else "0"),
                "chapters": self.clean_numeric(soup.select_one(".ep_count").text if soup.select_one(".ep_count") else "0"),
                "is_19": 1 if soup.select_one(".badge-19, .icon-19") else 0,
                "is_plus": 1 if soup.select_one(".badge-plus, .plus_icon") else 0,
                "is_completed": 1 if "완결" in soup.get_text() else 0,
                "tags_en": [t.get_text(strip=True) for t in soup.select(".tag_item")],
                "url": url
            }

            # 4. Quality Gate
            if not is_high_quality(metadata, int(novel_id)):
                return "Filtered"

            self.db.save_novel(novel_id, metadata)
            time.sleep(1.2)
            return "Saved"

        except Exception as e:
            return f"System Error: {str(e)}"
