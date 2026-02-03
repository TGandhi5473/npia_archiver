import re
import time
import random
import json
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth # New Class
from deep_translator import GoogleTranslator
from .database import NovelDB

class NovelArchiver:
    def __init__(self):
        self.db = NovelDB()
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

        # Initialize the Stealth configuration once
        stealth_config = Stealth()

        with sync_playwright() as p:
            try:
                # 1. Launch Browser
                browser = p.chromium.launch(headless=True)
                
                # 2. Create Context with human-like properties
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="ko-KR",
                    timezone_id="Asia/Seoul"
                )
                
                # 3. APPLY STEALTH TO THE CONTEXT
                # This is the 2026 way: Use apply_stealth_sync on the context object
                stealth_config.apply_stealth_sync(context)
                
                page = context.new_page()
                url = f"{self.base_url}{novel_id}"
                
                # 4. Navigate with generous timeout for Cloudflare
                response = page.goto(url, wait_until="networkidle", timeout=45000)
                
                content = page.content().lower()
                if "just a moment" in content or response.status == 403:
                    browser.close()
                    return "🛑 403: Cloudflare Blocked"

                # 5. Extraction Logic
                title_el = page.locator(".title").first
                if title_el.count() == 0:
                    browser.close()
                    return "🗑️ Error: Content Not Found"

                # (Keep all your existing metadata extraction here...)
                title = title_el.inner_text().strip()
                writer = page.locator(".writer").first.inner_text().strip() if page.locator(".writer").count() > 0 else "Unknown"
                ko_tags = [t.inner_text().replace("#", "") for t in page.locator(".tag_item").all()]
                
                metadata = {
                    "title": title,
                    "writer": writer,
                    "views": self.clean_numeric(page.locator(".view_count").first.inner_text() if page.locator(".view_count").count() > 0 else "0"),
                    "chapters": self.clean_numeric(page.locator(".ep_count").first.inner_text() if page.locator(".ep_count").count() > 0 else "0"),
                    "is_19": 1 if page.locator(".badge-19, .icon-19").count() > 0 else 0,
                    "is_plus": 1 if page.locator(".badge-plus, .plus_icon").count() > 0 else 0,
                    "is_completed": 1 if "완결" in content else 0,
                    "tags_ko": ko_tags,
                    "tags_en": [self.translator.translate(t) for t in ko_tags],
                    "url": url
                }

                self.db.save_novel(novel_id, metadata)
                
                time.sleep(random.uniform(2, 4))
                browser.close()
                return "Saved"

            except Exception as e:
                return f"❌ Error: {str(e)[:40]}"

    def clean_numeric(self, value):
        text = re.sub(r'[^0-9.]', '', str(value).replace(',', ''))
        if '만' in str(value): return int(float(text) * 10000)
        return int(float(text)) if text else 0
