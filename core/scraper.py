# ==========================================
# FILE: core/scraper.py
# ==========================================
import requests
from bs4 import BeautifulSoup
import time
import random
import re
from .filters import is_high_quality
from .translator import translate_tags
from .database import DatabaseManager

class NovelArchiver:
    def __init__(self):
        self.db = DatabaseManager()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def _clean_number(self, text):
        if not text: return 0
        clean_str = re.sub(r'[^\d]', '', text)
        return int(clean_str) if clean_str else 0

    def scrape_novel(self, novel_id):
        if self.db.is_archived(novel_id): return "Cached"
        if self.db.is_blacklisted(novel_id): return "Blacklisted"

        url = f"https://novelpia.com/novel/{novel_id}"
        try:
            time.sleep(random.uniform(1.1, 1.6))
            resp = requests.get(url, headers={"User-Agent": random.choice(self.user_agents)}, timeout=10)
            
            if resp.status_code == 404:
                self.db.blacklist_id(novel_id, "404")
                return "404"
            if resp.status_code != 200: return f"Error {resp.status_code}"

            soup = BeautifulSoup(resp.text, 'html.parser')
            title_el = soup.find('div', class_='epnew-novel-title')
            writer_el = soup.find('div', class_='epnew-writer')
            if not title_el: return "Parse Error"

            # Stats Extraction
            chapters, views = 0, 0
            for s in soup.find_all('span'):
                txt = s.get_text(strip=True)
                if txt == '회차':
                    val = s.find_next_sibling('span')
                    if val: chapters = self._clean_number(val.text)
                elif txt == '조회':
                    val = s.find_next_sibling('span')
                    if val: views = self._clean_number(val.text)

            # Badge/Status Checking
            full_text = soup.get_text()
            is_19 = 1 if soup.find('span', class_='badge-19') or '19' in full_text else 0
            is_plus = 1 if soup.find('span', class_='badge-plus') or 'PLUS' in full_text else 0
            is_completed = 1 if '완결' in full_text and '연재중' not in full_text else 0

            # Tags
            tag_set = set()
            for el in soup.select('a.tag-item, .novel_tag_area a, .tag-area a'):
                for part in el.get_text(strip=True).split('#'):
                    if part.strip(): tag_set.add(part.strip())

            metadata = {
                "id": novel_id,
                "title": title_el.get_text(strip=True),
                "writer": writer_el.get_text(strip=True).replace('작가명', ''),
                "chapters": chapters,
                "views": views,
                "tags_kr": sorted(list(tag_set)),
                "tags_en": translate_tags(list(tag_set)),
                "url": url,
                "is_completed": is_completed,
                "is_19": is_19,
                "is_plus": is_plus
            }

            if "카라멜돌체라떼" in metadata['writer'] or is_high_quality(metadata, novel_id):
                self.db.save_novel(metadata)
                return "Saved"
            else:
                self.db.blacklist_id(novel_id, "Filtered")
                return "Filtered"

        except Exception as e:
            return f"Error: {str(e)}"
