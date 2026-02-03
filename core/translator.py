# core/translator.py

TAG_MAP = {
    # Genres & Settings
    "판타지": "Fantasy",
    "중세": "Medieval",
    "현대": "Modern",
    "현판": "Modern Fantasy",
    "무협": "Martial Arts",
    "전생": "Previous Life",
    "일상": "Slice of Life",
    
    # Adult & High-Level (As requested)
    "고수위": "High-Explicit",
    "하드": "Hardcore",
    "하드코어": "Hardcore",
    "능욕": "Violation",
    "조교": "Training",
    "약한조교": "Soft-Training",
    "관음": "Voyeurism",
    "근친": "Incest",
    "엄마": "Mother",
    "여동생": "Sister",
    "MILF": "MILF",
    "마사지": "Massage",
    "NTL": "Netori",
    "MTR": "Netorae",
    
    # Tropes
    "하렘": "Harem",
    "집착": "Obsession",
    "순애": "Pure-Love",
    "피폐": "Angst",
    "아카데미": "Academy",
    "TS": "Gender-Bender"
}

def translate_tags(kr_tags):
    """
    Translates KR tags. 
    If not in map, keeps KR so the data isn't 'omitted'.
    """
    if not kr_tags:
        return []
    return [TAG_MAP.get(tag, f"KR_{tag}") for tag in kr_tags]
