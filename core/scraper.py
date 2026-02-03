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
        """Loads existing data from the local JSON file."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _clean_number(self, text):
        """
        The 'Bulletproof' Cleaner.
        Removes every single character that isn't a digit (0-9).
        Converts '34차' -> '34' and '1,200회' -> '1200'
        """
        if not text:
            return 0
        # This regex removes anything NOT a digit
        clean_str = re.sub(r'[^\d]', '', text)
        try:
            return int(clean_str) if clean_str else 0
        except ValueError:
            return 0

    def get_headers(self):
        """Generates fresh headers to bypass simple bot checks."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://novelpia.com/",
            "Connection": "keep-alive"
        }

    def scrape_novel(self, novel_id):
        """Main scraping logic for a single Novel ID."""
        str_id = str(novel_id)
        
        # 1. Smart Cache Check
        if str_id in self.data:
            return "Cached"

        url = f"https://novelpia.com/novel/{novel_id}"
        
        try:
            # Politeness delay
            time.sleep(random.uniform(1.0, 1.8))
            
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 404:
                return "404"
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # --- Basic Info Extraction ---
                title_el = soup.find('div', class_='epnew-novel-title')
                writer_el = soup.find('div', class_='epnew-writer')
                
                if not title_el:
                    return "Parse Error"
                
                title = title_el.get_text(strip=True)
                writer = writer_el.get_text(strip=True) if writer_el else "Unknown"

                # --- Numeric Info Extraction (The '차' Fix) ---
                chapters = 0
                views = 0
                
                # Novelpia labels are usually in spans
                labels = soup.find_all('span')
                for s in labels:
                    label_text = s.get_text(strip=True)
                    if label_text == '회차':
                        val = s.find_next_sibling('span')
                        if val: chapters = self._clean_number(val.text)
                    elif label_text == '조회':
                        val = s.find_next_sibling('span')
                        if val: views = self._clean_number(val.text)

                # --- Tag Extraction ---
                tags_kr = [t.get_text(strip=True).replace('#', '') 
                           for t in soup.find_all('a', class_='tag-item')]

                metadata = {
                    "id": novel_id,
                    "title": title,
                    "writer": writer,
                    "chapters": chapters,
                    "views": views,
                    "tags_kr": tags_kr,
                    "is_19": soup.find('span', class_='b_19') is not None,
                    "is_plus": soup.find('span', class_='b_plus') is not None,
                    "url": url,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }

                # 2. Quality Filter Logic
                # Logic: Always keep the specific author, else check sliding scale
                if "카라멜돌체라떼" in writer or is_high_quality(metadata, novel_id):
                    self.data[str_id] = metadata
                    self._save()
                    return "Saved"
                else:
                    return "Filtered"

        except Exception as e:
            return f"Error: {str(e)}"

    def _save(self):
        """Atomic save to the local JSON file."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
