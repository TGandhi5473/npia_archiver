import time
import random
import re
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from deep_translator import GoogleTranslator
from .database import NovelDB

class NovelArchiver:
    def __init__(self):
        self.db = NovelDB()
        self.base_url = "https://novelpia.com/novel/"
        self.translator = GoogleTranslator(source='ko', target='en')
        self.tag_map = {} # Should be loaded from JSON if you have it

    def scrape_novel(self, novel_id):
        if self.db.is_cached(novel_id):
            return "Cached"

        with sync_playwright() as p:
            # Launching a real browser to bypass Cloudflare Turnstile
            browser = p.chromium.launch(headless=True) 
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()
            stealth_sync(page) # Hides automation signatures

            try:
                url = f"{self.base_url}{novel_id}"
                # Increase timeout to 30s to allow Cloudflare to "verify" you
                response = page.goto(url, wait_until="networkidle", timeout=30000)
                
                # DIAGNOSTIC: Check if we are stuck on a challenge page
                if "just a moment" in page.content().lower() or response.status == 403:
                    browser.close()
                    return "🛑 403: Cloudflare Block"

                # Extraction using Playwright selectors
                title = page.locator(".title").inner_text() if page.locator(".title").count() > 0 else None
                if not title:
                    browser.close()
                    return "🗑️ Error: Content Not Found (Private?)"

                # Metadata Parsing
                ko_tags = [t.inner_text().replace("#", "") for t in page.locator(".tag_item").all()]
                
                metadata = {
                    "title": title.strip(),
                    "writer": page.locator(".writer").first.inner_text().strip(),
                    "views": self.clean_numeric(page.locator(".view_count").first.inner_text()),
                    "chapters": self.clean_numeric(page.locator(".ep_count").first.inner_text()),
                    "is_19": 1 if page.locator(".badge-19, .icon-19").count() > 0 else 0,
                    "is_plus": 1 if page.locator(".badge-plus, .plus_icon").count() > 0 else 0,
                    "is_completed": 1 if "완결" in page.content() else 0,
                    "tags_ko": ko_tags,
                    "tags_en": [self.translator.translate(t) for t in ko_tags],
                    "url": url
                }

                self.db.save_novel(novel_id, metadata)
                browser.close()
                return "Saved"

            except Exception as e:
                browser.close()
                return f"❌ Error: {str(e)[:30]}"

    def clean_numeric(self, val):
        digits = re.sub(r'[^0-9.]', '', str(val))
        if '만' in str(val): return int(float(digits) * 10000)
        return int(float(digits)) if digits else 0
