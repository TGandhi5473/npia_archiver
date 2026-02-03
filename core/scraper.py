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
    def __init__(self, storage_path='data/metadata.json', skip_path='data/skipped_ids.json'):
        self.storage_path = storage_path
        self.skip_path = skip_path
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        # Initialize storage and the "Skip List"
        self.data = self._load_json(self.storage_path, default_type=dict)
        self.skipped_ids = set(self._load_json(self.skip_path, default_type=list))

    def _load_json(self, path, default_type=dict):
        """Helper to load JSON safely from an absolute path."""
        abs_path = self._get_abs_path(path)
        if os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return default_type()
        return default_type()

    def _get_abs_path(self, relative_path):
        """Ensures we are always looking at the right folder regardless of where CLI started."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(base_dir, "..", relative_path))

    def _clean_number(self, text):
        """Strips all non-numeric characters to prevent '34차' errors."""
        if not text: return 0
        clean_str = re.sub(r'[^\d]', '', text)
        return int(clean_str) if clean_str else 0

    def scrape_novel(self, novel_id):
        str_id = str(novel_id)
        
        # 1. Performance Check (Instant Skip)
        if str_id in self.data:
            return "Cached"
        if novel_id in self.skipped_ids:
            return "Blacklisted"

        url = f"https://novelpia.com/novel/{novel_id}"
        try:
            time.sleep(random.uniform(1.2, 1.8))
            headers = {"User-Agent": random.choice(self.user_agents), "Referer": "https://novelpia.com/"}
            resp = requests.get(url, headers=headers, timeout=10)
            
            # 2. Handle Dead IDs (Save to Skip List)
            if resp.status_code == 404:
                self.skipped_ids.add(novel_id)
                self._save_skipped()
                return "404 (Blacklisted)"

            if resp.status_code != 200: return f"Error {resp.status_code}"

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

            # --- Tag Logic (The Multi-Splitter) ---
            tag_set = set()
            for el in soup.select('a.tag-item, .novel_tag_area a, .tag-area a'):
                for part in el.get_text(strip=True).split('#'):
                    if part.strip(): tag_set.add(part.strip())

            final_kr_tags = sorted(list(tag_set))
            
            metadata = {
                "id": novel_id,
                "title": title_el.get_text(strip=True),
                "writer": writer_el.get_text(strip=True) if writer_el else "Unknown",
                "chapters": chapters,
                "views": views,
                "tags_kr": final_kr_tags,
                "tags_en": translate_tags(final_kr_tags),
                "url": url,
                "timestamp": time.strftime("%Y-%m-%d")
            }

            # 3. Quality Filter (Blacklist if fails)
            if "카라멜돌체라떼" in metadata['writer'] or is_high_quality(metadata, novel_id):
                self.data[str_id] = metadata
                self._save_data()
                return "Saved"
            else:
                self.skipped_ids.add(novel_id)
                self._save_skipped()
                return "Filtered (Blacklisted)"

        except Exception as e:
            return f"Error: {str(e)}"

    def _save_data(self):
        path = self._get_abs_path(self.storage_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    def _save_skipped(self):
        path = self._get_abs_path(self.skip_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(list(self.skipped_ids), f)
