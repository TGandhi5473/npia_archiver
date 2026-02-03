import cloudscraper
import json
import os
import time
import re
import random
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
from .database import NovelDB

class NovelArchiver:
    def __init__(self):
        self.db = NovelDB()
        # Initialize with specific browser fingerprint
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        # Force Korean headers to look like a local user
        self.scraper.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://novelpia.com/",
            "Cache-Control": "max-age=0"
        })
        self.base_url = "https://novelpia.com/novel/"
        self.translator = GoogleTranslator(source='ko', target='en')
        self.tag_map_path = "tag_map.json"
        self.tag_map = self.load_tag_map()

    def load_tag_map(self):
        if os.path.exists(self.tag_map_path):
            with open(self.tag_map_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_tag_map(self):
        with open(self.tag_map_path, 'w', encoding='utf-8') as f:
            json.dump(self.tag_map, f, ensure_ascii=False, indent=4)

    def translate_tag(self, ko_tag):
        if ko_tag in self.tag_map: return self.tag_map[ko_tag]
        try:
            en_tag = self.translator.translate(ko_tag)
            self.tag_map[ko_tag] = en_tag
            self.save_tag_map()
            return en_tag
        except: return ko_tag

    def clean_numeric(self, value):
        if not value: return 0
        text = str(value).replace(',', '').strip()
        if '만' in text:
            try: return int(float(text.replace('만', '')) * 10000)
            except: return 0
        digits = re.sub(r'[^0-9]', '', text)
        return int(digits) if digits else 0

    def scrape_novel(self, novel_id):
        # 1. Simple Cache Check
        if self.db.is_cached(novel_id):
            return "Cached"

        try:
            url = f"{self.base_url}{novel_id}"
            response = self.scraper.get(url, timeout=15)
            
            # Explicit 403 / Cloudflare Detection
            if response.status_code == 403 or "cf-browser-verification" in response.text:
                return "403: Forbidden/Bot Detection"
            
            if response.status_code == 404: 
                return "Parse Error: Removed"

            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.select_one(".title")
            
            # Direct Title Check (No quality filters)
            if not title_tag:
                return "Parse Error: Novel Removed"

            # 2. Extract Metadata
            ko_tags = [t.get_text(strip=True).replace("#", "") for t in soup.select(".tag_item")]
            en_tags = [self.translate_tag(tag) for tag in ko_tags]

            metadata = {
                "title": title_tag.get_text(strip=True),
                "writer": soup.select_one(".writer").get_text(strip=True) if soup.select_one(".writer") else "Unknown",
                "views": self.clean_numeric(soup.select_one(".view_count").text if soup.select_one(".view_count") else "0"),
                "chapters": self.clean_numeric(soup.select_one(".ep_count").text if soup.select_one(".ep_count") else "0"),
                "is_19": 1 if soup.select_one(".badge-19, .icon-19") else 0,
                "is_plus": 1 if soup.select_one(".badge-plus, .plus_icon") else 0,
                "is_completed": 1 if "완결" in response.text else 0,
                "tags_ko": ko_tags,
                "tags_en": en_tags,
                "url": url
            }

            # 3. Direct Save
            self.db.save_novel(novel_id, metadata)
            
            # 4. Human-like Jitter Delay
            time.sleep(random.uniform(2.0, 5.0))
            return "Saved"

        except Exception as e:
            return f"Error: {str(e)}"
