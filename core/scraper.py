import requests
from bs4 import BeautifulSoup
import json
import os
import time
import random
from .filters import is_high_quality

class NovelArchiver:
    def __init__(self, storage_path='data/metadata.json'):
        self.storage_path = storage_path
        # List of modern user agents to rotate
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        ]
        self.data = self._load_data()

    def _load_data(self):
        """Loads the existing JSON cache if it exists."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def get_headers(self):
        """Generates fresh headers for each request."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Referer": "https://novelpia.com/",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def scrape_novel(self, novel_id):
        """
        Scrapes a single novel ID. 
        Returns 'Cached', 'Saved', 'Filtered', or '404'.
        """
        str_id = str(novel_id)
        
        # 1. Check if already archived
        if str_id in self.data:
            return "Cached"

        url = f"https://novelpia.com/novel/{novel_id}"
        
        try:
            # Short delay to be polite
            time.sleep(random.uniform(1.0, 1.5))
            
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 404:
                return "404"
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract Title
                title_el = soup.find('div', class_='epnew-novel-title')
                if not title_el:
                    return "Error"
                
                # Extract Writer
                writer_el = soup.find('div', class_='epnew-writer')
                writer = writer_el.get_text(strip=True) if writer_el else "Unknown"

                # Extract Chapters & Views (Sibling Logic)
                chapters = 0
                views = 0
                
                chap_label = soup.find('span', string='회차')
                if chap_label:
                    val = chap_label.find_next_sibling('span').get_text(strip=True)
                    chapters = int(val.replace(',', '').replace('회', ''))

                view_label = soup.find('span', string='조회')
                if view_label:
                    val = view_label.find_next_sibling('span').get_text(strip=True)
                    views = int(val.replace(',', ''))

                # Extract Tags (Korean list)
                tags_kr = [t.get_text(strip=True).replace('#', '') 
                           for t in soup.find_all('a', class_='tag-item')]

                # Metadata Object
                metadata = {
                    "id": novel_id,
                    "title": title_el.get_text(strip=True),
                    "writer": writer,
                    "chapters": chapters,
                    "views": views,
                    "tags_kr": tags_kr,
                    "is_19": soup.find('span', class_='b_19') is not None,
                    "is_plus": soup.find('span', class_='b_plus') is not None,
                    "url": url
                }

                # 2. Apply the Quality Filter (from filters.py)
                # Ensure target writer '카라멜돌체라떼' is ALWAYS saved
                if "카라멜돌체라떼" in writer or is_high_quality(metadata, novel_id):
                    self.data[str_id] = metadata
                    self._save()
                    return "Saved"
                else:
                    return "Filtered"

        except Exception as e:
            print(f"Error scraping {novel_id}: {e}")
            return "Error"

    def _save(self):
        """Atomic write to JSON."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
