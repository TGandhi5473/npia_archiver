def is_high_quality(metadata, novel_id):
    """
    Sliding scale filter: Older IDs require higher engagement.
    """
    views = metadata.get('views', 0)
    chapters = metadata.get('chapters', 0)
    
    # Thresholds: Older novels (ID < 300k) need higher stats
    if novel_id < 300000:
        return views > 50000 and chapters > 50
    else:
        # Newer novels are easier to archive
        return views > 5000 and chapters > 10
