import re
import time
import random
import json
import os
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth # Updated class-based import
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

    def clean_numeric(self, value):
        if not value: return 0
        text = re.sub(r'[^0-9.]', '', str(value).replace(',', ''))
        if '만' in str(value):
            try: return int(float(text) * 10000)
            except: return 0
        return int(float(text)) if text else 0

    def scrape_novel(self, novel_id):
        if self.db.is_cached(novel_id):
            return "Cached"

        # 1. Initialize Stealth Engine
        stealth = Stealth()

        with sync_playwright() as p:
            # 2. Use the 'use_sync' wrapper to apply stealth globally
            with stealth.use_sync(p) as p_stealth:
                browser = p_stealth.chromium.launch(headless=True)
                
                # Mimic a high-trust Korean Windows user
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    locale="ko-KR",
                    timezone_id="Asia/Seoul"
                )
                
                page = context.new_page()

                try:
                    url = f"{self.base_url}{novel_id}"
                    # Increased timeout to allow Cloudflare Turnstile to verify
                    response = page.goto(url, wait_until="networkidle", timeout=45000)
                    
                    # DIAGNOSTIC: Detect Challenge Pages
                    content = page.content().lower()
                    if "just a moment" in content or "cloudflare" in content or response.status == 403:
                        browser.close()
                        return "🛑 403: Cloudflare Blocked
