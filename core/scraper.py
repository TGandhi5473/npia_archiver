import asyncio
import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        # 2026-optimized headers to mimic a real Chromium browser
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            "Referer": "https://novelpia.com/",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
        }

    def _safe_extract(self, soup, alt_text):
        """Helper to find numbers next to specific icons (선호, 회차, 알람)"""
        icon = soup.find("img", alt=alt_text)
        if not icon: return None
        
        # Move to the container holding the number
        container = icon.find_next("span")
        if not container: return None
        
        # Clean text: "1,234" -> 1234
        val_text = container.get_text(strip=True).replace(',', '')
        match = re.search(r'\d+', val_text)
        return int(match.group()) if match else 0

    def scrape_novel(self, novel_id):
        """Synchronous wrapper for Streamlit loop compatibility"""
        return asyncio.run(self._async_scrape(novel_id))

    async def _async_scrape(self, novel_id):
        if self.db.check_exists(novel_id):
            return "ALREADY_KNOWN"

        async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
            try:
                url = f"{self.base_url}{novel_id}"
                # Random jitter to avoid rate limits
                await asyncio.sleep(0.1) 
                
                resp = await client.get(url, timeout=10.0)
                
                if resp.status_code == 404 or "삭제된 소설" in resp.text:
                    self.db.add_to_blacklist(novel_id, "GHOST_ID")
                    return "BLACKLISTED (GHOST)"
                
                if resp.status_code != 200:
                    return f"HTTP_{resp.status_code}"

                soup = BeautifulSoup(resp.text, 'lxml') # Use lxml for 2026 speed

                # 1. DATA EXTRACTION
                fav = self._safe_extract(soup, "선호")
                ep = self._safe_extract(soup, "회차")
                al = self._safe_extract(soup, "알람")

                # 2. THE GATEKEEPER FILTERS
                # We filter here so the DB only contains potential hits
                if fav is None or ep is None:
                    self.db.add_to_blacklist(novel_id, "LAYOUT_ERROR")
                    return "BLACKLISTED (MISSING_DATA)"

                if fav < 50 or ep < 5:
                    self.db.add_to_blacklist(novel_id, "LOW_SIGNAL")
                    return "REJECTED (Low Stats)"

                # 3. SUCCESS PATH
                title_tag = soup.select_one(".title")
                author_tag = soup.select_one(".author")
                
                data = {
                    'id': novel_id,
                    'title': title_tag.get_text(strip=True) if title_tag else "Unknown",
                    'author': author_tag.get_text(strip=True) if author_tag else "Unknown",
                    'fav': fav,
                    'ep': ep,
                    'al': al or 0,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': ", ".join([t.get_text(strip=True) for t in soup.select(".tag_item")]),
                    'is_19': 1 if soup.select_one(".badge-19") else 0,
                    'is_plus': 1 if soup.select_one(".badge-plus") else 0,
                    'url': url,
                    'date': datetime.now()
                }

                self.db.save_novel(data)
                return "SUCCESS (SAVED)"

            except Exception as e:
                return f"CRASH: {str(e)[:30]}"
