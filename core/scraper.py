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
        # Rotating User-Agents to prevent bot detection
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        self.data = self._load_data()

    def _load_data(self):
        """Loads the existing JSON cache."""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _clean_number(self, text):
        """Extracts only digits from strings like '34차', '1,200회', or '10,000'."""
        if not text:
            return 0
        digits = "".join(re.findall(r'\d+', text))
        return int(digits) if digits else 0

    def get_headers(self):
        """Fresh headers to look like a real browser."""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://novelpia.com/",
            "Connection": "keep-alive"
        }

    def scrape_novel(self, novel_id):
        """Scrapes metadata and saves if it passes filters."""
        str_id = str(novel_id)
        
        # 1. Skip if already in our local JSON
        if str_id in self.data:
            return "Cached"

        url = f"https://novelpia.com/novel/{novel_id}"
        
        try:
            # Random delay to avoid IP blocks
            time.sleep(random.uniform(1.2, 2.0))
            
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 404:
                return "404"
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Title & Writer Extraction
                title_el = soup.find('div', class_='epnew-novel-title')
                writer_el = soup.find('div', class_='epnew-writer')
                
                if not title_el:
                    return "Parse Error"
                
                title = title_el.get_text(strip=True)
                writer = writer_el.get_text(strip=True) if writer_el else "Unknown"

                # Numeric Extraction using the new _clean_number helper
                chapters = 0
                views = 0
                
                # Find the label, then find the value next to it
                chap_label = soup.find('span', string='회차')
                if chap_label:
                    raw_chap = chap_label.find_next_sibling('span').get_text(strip=True)
                    chapters = self._clean_number(raw_chap)

                view_label = soup.find('span', string='조회')
                if view
