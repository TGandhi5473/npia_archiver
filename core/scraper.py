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
        # Initialize the SQLite Database Manager
        self.db = DatabaseManager()
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def _clean_number(self, text):
        """Strips all non-numeric characters (e.g., '34차' -> 34)."""
        if not text: return 0
        clean_str = re.sub(r'[^\d]', '', text)
        return int(clean_str) if clean_str else 0

    def scrape_novel(self, novel_id):
        # 1. Instant Check (No web request needed)
        if self.db.is_archived(novel_id):
            return "Cached"
        if self.db.is_blacklisted(novel_id):
            return "Blacklisted"

        url = f"https://novelpia.com/novel/{novel_id}"
        try:
            # Human-like delay
            time.sleep(random.uniform(1.1, 1.7))
            
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Referer": "https://novelpia.com/"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            
            # 2. Handle 404s (Add to Blacklist so we never check again)
            if resp.status_code == 404:
                self.db.blacklist_id(novel_id, "404 Not Found")
                return "404 (Blacklisted)"

            if resp.status_code != 200: 
                return f"HTTP Error {resp.status_code}"

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # --- Content Extraction ---
            title_el = soup.find('div', class_='epnew-novel-title')
            writer_el = soup.find('div', class_='epnew-writer')
            if not title_el: return "Parse Error"

            # --- Chapters & Views ---
            chapters, views = 0, 0
            for s in soup.find_all('span'):
                txt = s.get_text(strip=True)
                if txt == '회차':
                    val = s.find_next_sibling('span')
                    if val: chapters = self._clean_number(val.text)
                elif txt == '조회':
                    val = s.find_next_sibling('span')
                    if val: views = self._clean_number(val.text)

            # --- Tag Logic (Splitting & Translation) ---
            tag_set = set()
            # Selects multiple possible tag locations
            tag_els = soup.select('a.tag-item, .novel_tag_area a, .tag-area a')
            for el in tag_els:
                raw_text = el.get_text(strip=True)
                # Split clumped tags like #Fantasy#Harem
                for part in raw_text.split('#'):
                    clean_tag = part.strip()
                    if clean_tag: tag_set.add(clean_tag)

            final_kr_tags = sorted(list(tag_set))
            final_en_tags = translate_tags(final_kr_tags)

            metadata = {
                "id": novel_id,
                "title": title_el.get_text(strip=True),
                "writer": writer_el.get_text(strip=True) if writer_el else "Unknown",
                "chapters": chapters,
                "views": views,
                "tags_kr": final_kr_tags,
                "tags_en": final_en_tags,
                "url": url
            }

            # 3. Quality Filter
            # Always save specific authors OR check quality
            if "카라멜돌체라떼" in metadata['writer'] or is_high_quality(metadata, novel_id):
                self.db.save_novel(metadata)
                return "Saved"
            else:
                # If it sucks, blacklist it so we don't waste time next time
                self.db.blacklist_id(novel_id, "Filtered (Low Quality)")
                return "Filtered (Blacklisted)"

        except Exception as e:
            return f"Error: {str(e)}"
