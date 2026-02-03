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
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
        )
        # Mimic a high-authority browser session
        self.scraper.headers.update({
            "Referer": "https://novelpia.com/",
            "Accept-Language": "ko-KR,ko;q=0.9",
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

    def scrape_novel(self, novel_id):
        if self.db.is_cached(novel_id):
            return "Cached"

        try:
            url = f"{self.base_url}{novel_id}"
            response = self.scraper.get(url, timeout=15)
            
            # --- THE 403 DIAGNOSTIC CHECK ---
            html_content = response.text.lower()
            
            if response.status_code == 403:
                return "🚨 403: Hard Block"
            
            if "checking your browser" in html_content or "cloudflare" in html_content:
                return "🛡️ 403: Cloudflare Challenge (Silent)"
            
            if "login" in response.url or "member/login" in html_content:
                return "🔑 403: Login Required"

            soup = BeautifulSoup(response.text, 'html.parser')
            title_tag = soup.select_one(".title")
            
            # If we get here but have no title, the site structure likely changed
            if not title_tag:
                return "❓ Error: Elements Not Found (Structure Change?)"

            # Extraction
            ko_tags = [t.get_text(strip=True).replace("#", "") for t in soup.select(".tag_item")]
            en_tags = [self.tag_map.get(t) or self.translator.translate(t) for t in ko_tags]
            
            # Update map for new tags
            for ko, en in zip(ko_tags, en_tags):
                if ko not in self.tag_map:
                    self.tag_map[ko] = en
            self.save_tag_map()

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

            self.db.save_novel(novel_id, metadata)
            time.sleep(random.uniform(2, 4))
            return "Saved"

        except Exception as e:
            return f"❌ System Error: {str(e)}"

    def clean_numeric(self, value):
        text = re.sub(r'[^0-9.]', '', str(value).replace(',', ''))
        if '만' in str(value): return int(float(text) * 10000)
        return int(float(text)) if text else 0
