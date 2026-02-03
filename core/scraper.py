import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import re
from .filters import is_high_quality
from .translator import translate_tags

class NovelArchiver:
    def __init__(self, storage_path='data/metadata.json'):
        self.storage_path = storage_path
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.data = self._load_data()

    def _load_data(self):
        """Loads existing data; creates directory if missing."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _clean_number(self, text):
        """
        Removes all non-numeric characters (like '차', '회', commas).
        '34차' -> 34
        """
        if not text:
            return 0
        clean_str = re.sub(r'[^\d]', '', text)
        try:
            return int(clean_str) if clean_str else 0
        except ValueError:
            return 0

    def scrape_novel(self, novel_id):
        str_id = str(novel_id)
        if str_id in self.data:
            return "Cached"

        url = f"https://novelpia.com/novel/{novel_id}"
        try:
            time.sleep(random.uniform(1.2, 2.0))
            headers = {
                "User-Agent": random.choice(self.user_agents),
                "Referer": "https://novelpia.com/"
            }
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 404: return "404"
            if resp.status_code != 200: return f"HTTP {resp.status_code}"

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # --- Meta Extraction ---
            title_el = soup.find('div', class_='epnew-novel-title')
            writer_el = soup.find('div', class_='epnew-writer')
            if not title_el: return "Structure Error"

            # --- Numeric Data (Chapters/Views) ---
            chapters = 0
            views = 0
            info_spans = soup.find_all('span')
            for s in info_spans:
                txt = s.get_text(strip=True)
                if txt == '회차':
                    val = s.find_next_sibling('span')
                    if val: chapters = self._clean_number(val.text)
                elif txt == '조회':
                    val = s.find_next_sibling('span')
                    if val: views = self._clean_number(val.text)

            # --- Tag Handling (The Splitter) ---
            # Handles both individual links and clumped text like #Tag1#Tag2
            raw_tag_elements = soup.select('a.tag-item, .novel_tag_area a, .tag-area a')
            tag_set = set()

            for el in raw_tag_elements:
                raw_text = el.get_text(strip=True)
                # Split by '#' to catch clumped tags and strip whitespace
                parts = [p.strip() for p in raw_text.split('#') if p.strip()]
                tag_set.update(parts)

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
                "url": url,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # --- Filtering & Saving ---
            if "카라멜돌체라떼" in metadata['writer'] or is_high_quality(metadata, novel_id):
                self.data[str_id] = metadata
                self._save()
                return "Saved"
            
            return "Filtered"

        except Exception as e:
            return f"Error: {str(e)}"

    def _save(self):
        """Saves data using an absolute path to avoid directory confusion."""
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            # Path points to npia_archiver/data/metadata.json
            full_path = os.path.join(base_dir, "..", self.storage_path)
            
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Internal Save Error: {e}")
