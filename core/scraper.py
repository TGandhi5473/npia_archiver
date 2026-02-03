import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
import re
from .filters import is_high_quality

class NovelArchiver:
    def __init__(self, storage_path='data/metadata.json'):
        self.storage_path = storage_path
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _clean_number(self, text):
        """
        Aggressively removes all non-numeric characters.
        '34차' -> '34'
        '1,250회' -> '1250'
        """
        if not text:
            return 0
        # This keeps ONLY digits 0-9 and removes everything else (Korean, commas, etc.)
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
            time.sleep(random.uniform(1.0, 1.8))
            headers = {"User-Agent": random.choice(self.user_agents), "Referer": "https://novelpia.com/"}
            resp = requests.get(url, headers=headers, timeout=10)
            
            if resp.status_code == 404: return "404"
            if resp.status_code != 200: return f"Error {resp.status_code}"

            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # --- Robust Extraction ---
            title_el = soup.find('div', class_='epnew-novel-title')
            writer_el = soup.find('div', class_='epnew-writer')
            if not title_el: return "Structure Change"

            # Use the helper for both Chapters and Views
            chapters = 0
            views = 0
            
            # Extract Chapters
            chap_span = soup.find('span', string='회차')
            if chap_span:
                raw_chap = chap_span.find_next_sibling('span').get_text(strip=True)
                chapters = self._clean_number(raw_chap)

            # Extract Views
            view_span = soup.find('span', string='조회')
            if view_span:
                raw_view = view_span.find_next_sibling('span').get_text(strip=True)
                views = self._clean_number(raw_view)

            metadata = {
                "id": novel_id,
                "title": title_el.get_text(strip=True),
                "writer": writer_el.get_text(strip=True) if writer_el else "Unknown",
                "chapters": chapters,
                "views": views,
                "tags_kr": [t.get_text(strip=True).replace('#', '') for t in soup.find_all('a', class_='tag-item')],
                "url": url
            }

            if "카라멜돌체라떼" in metadata['writer'] or is_high_quality(metadata, novel_id):
                self.data[str_id] = metadata
                self._save()
                return "Saved"
            return "Filtered"

        except Exception as e:
            return f"Error: {str(e)}"

    def _save(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
