# Initial Map - user will expand this over time
TAG_MAP = {
    "판타지": "Fantasy",
    "하렘": "Harem",
    "성인": "19+",
    "로맨스": "Romance",
    "현대": "Modern"
}

def get_english_tags(korean_tags):
    """Maps KR tags to EN. If missing, returns the KR tag."""
    return [TAG_MAP.get(tag, tag) for tag in korean_tags]

def identify_missing_tags(all_novels):
    """Finds tags that exist in metadata but aren't in our TAG_MAP."""
    seen_tags = set()
    for item in all_novels.values():
        seen_tags.update(item.get('tags_kr', []))
    
    return [t for t in seen_tags if t not in TAG_MAP]
