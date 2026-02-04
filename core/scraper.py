import httpx
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }

    def _extract_stats_from_script(self, soup):
        """
        New 2026 Logic: Searches for hidden JSON data or JS variables 
        where Novelpia stores 'expect_cnt' (Favs) and 'ep_count' (Eps).
        """
        # Search all script tags for keywords
        scripts = soup.find_all("script")
        for script in scripts:
            if not script.string: continue
            
            # Look for the internal data object (often called 'novel_data' or similar)
            # We use regex to find numbers assigned to keys like 'fav_cnt' or 'expect_cnt'
            fav_match = re.search(r'["\']?(?:expect_cnt|fav_cnt|fav)["\']?\s*[:=]\s*(\d+)', script.string)
            ep_match = re.search(r'["\']?(?:ep_cnt|ep_count|total_ep)["\']?\s*[:=]\s*(\d+)', script.string)
            
            if fav_match and ep_match:
                return int(fav_match.group(1)), int(ep_match.group(1))
        
        # Fallback: Scrape the visible body if script search fails
        return self._fallback_body_scrape(soup)

    def _fallback_body_scrape(self, soup):
        """If the hidden data is missing, we hunt for the numbers near Korean labels."""
        text = soup.get_text()
        fav = re.search(r'선호\s*([\d,]+)', text)
        ep = re.search(r'회차\s*([\d,]+)', text)
        
        f = int(fav.group(1).replace(',', '')) if fav else 0
        e = int(ep.group(1).replace(',', '')) if ep else 0
        return f, e

    def scrape_novel(self, novel_id):
        url = f"https://novelpia.com/novel/{novel_id}"
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url, timeout=10.0)
                soup = BeautifulSoup(resp.text, 'lxml')
                
                fav, ep = self._extract_stats_from_script(soup)

                if fav == 0 or ep == 0:
                    return f"REJECTED (Stats not found for {novel_id})"

                ratio = round(fav / ep, 2) if ep > 0 else 0
                
                # Save logic here...
                return f"SUCCESS (Ratio: {ratio})"
        except Exception as e:
            return f"SYSTEM ERROR: {str(e)[:25]}"
