import httpx
from bs4 import BeautifulSoup
import re
from datetime import datetime

class NovelpiaScraper:
    def __init__(self, db_manager):
        self.db = db_manager
        self.base_url = "https://novelpia.com/novel/"
        
        # Dead giveaway tags for 18+ classification based on your focus
        self.ADULT_RED_FLAGS = [
    # --- Original Base & Core NSFW ---
    "ntl", "ntr", "고수위", "조교", "능욕", "최면", 
    "관음", "역강간", "촉수", "근친", "절륜", "성인",
    "19금", "성인용", "R18", "야설", "에로", "섹스",

    # --- Hardcore & Fetish ---
    "하드코어", "애널", "피스팅", "착정", "방뇨", "펠라치오",
    "파이즈리", "상식개변", "임신", "모유", "암컷타락", "자위",
    "이종간", "수간", "이상성욕", "보추", "오토코노코", "후타나리",
    "폭유", "대물", "음마", "서큐버스", "몽마", "스타킹", "하이힐",

    # --- Power Dynamics & Dark Themes ---
    "노예", "세뇌", "강간", "윤간", "조교물", "MC물", "MC",
    "성접대", "강제암컷타락", "최면물", "노예시장", "복종", "굴복",
    "감금", "겁탈", "가스라이팅", "의존", "지배", "역조교", "마조",

    # --- Taboo & Specific Tropes ---
    "유사근친", "모녀", "불륜", "밀프", "유부녀", "쇼타", "오네쇼타",
    "정조역전", "남녀역전", "여공남수", "펨돔", "소프트펨돔", "변태",
    "신체개조", "암컷", "약물", "페티시", "성비불균형", "천박",

    # --- Slang & System Specific ---
    "떡타지", "떡협지", "오나홀", "딜도", "BDSM", "SM", "막장","SM", "BDSM", "떡타지", "하드", "강간", "막장", "몬무스", "지배",
    "육변기", "섹스판타지", "마조히스트", "애상", "처녀", "다크로맨스",
    "면간", "뽕빨", "색협지", "야노", "성관계진화", "신체결손",
    "섹스로강해짐", "섹슈얼전투", "배설통제", "심리지배", "모유플",
    "조건만남", "키스방", "스웨디시", "안마", "유흥", "임신플",
    "스와핑", "정조대", "커컬드", "피스팅", "음식플", "BBC", "야스",
    "착유", "거근", "구강", "펨섭", "노팬티", "멜돔", "넷토", "네토마조"
]
        
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121.0.0.0",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }

    def _extract_stats_and_tags(self, soup):
        full_text = soup.get_text()
        
        fav_m = re.search(r'선호\s*[:：]?\s*([\d,]+)', full_text)
        ep_m = re.search(r'회차\s*[:：]?\s*([\d,]+)', full_text)
        al_m = re.search(r'알람\s*[:：]?\s*([\d,]+)', full_text)
        
        def clean(m):
            return int(m.group(1).replace(',', '')) if m else 0

        tags_found = re.findall(r'#([가-힣a-zA-Z0-9]+)', full_text)
        tags_str = ",".join(list(set(tags_found)))

        return clean(fav_m), clean(ep_m), clean(al_m), tags_str

    def scrape_novel(self, novel_id):
        if self.db.check_exists(novel_id):
            return "SKIPPED (Existing)"

        url = f"{self.base_url}{novel_id}"
        try:
            with httpx.Client(headers=self.headers, follow_redirects=True) as client:
                resp = client.get(url, timeout=10.0)
                
                if resp.status_code == 404:
                    self.db.add_to_blacklist(novel_id, "404")
                    return "BLACKLISTED (404)"

                soup = BeautifulSoup(resp.text, 'lxml')
                fav, ep, al, tags = self._extract_stats_and_tags(soup)

                if fav < 10 or ep < 1:
                    self.db.add_to_blacklist(novel_id, "LOW_SIGNAL")
                    return "BLACKLISTED (Insufficient Data)"

                # --- 18+ LOGIC OVERRIDE ---
                is_18 = 1 if "19세" in resp.text else 0
                
                # Check tags for adult content (case-insensitive for ntl/ntr)
                tag_list = [t.lower() for t in tags.split(',')]
                if any(flag in tag_list for flag in self.ADULT_RED_FLAGS):
                    is_18 = 1
                # --------------------------

                title_meta = soup.find("meta", property="og:title")
                title = title_meta.get("content", "Unknown").replace("노벨피아 - ", "").split(" - ")[0] if title_meta else f"Novel_{novel_id}"

                data = {
                    'id': novel_id,
                    'title': title,
                    'author': "NPIA Scout",
                    'fav': fav,
                    'ep': ep,
                    'al': al,
                    'ratio': round(fav / ep, 2) if ep > 0 else 0,
                    'tags': tags,
                    'is_19': is_18,
                    'is_plus': 1 if "플러스" in resp.text or "plus" in resp.text.lower() else 0,
                    'url': url,
                    'date': datetime.now()
                }

                self.db.save_novel(data)
                return f"SUCCESS (18+: {'YES' if is_18 else 'NO'} | Ratio: {data['ratio']})"

        except Exception as e:
            return f"ERR: {str(e)[:20]}"
