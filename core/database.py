import sqlite3
from datetime import datetime
from collections import Counter

class NovelDB:
    def __init__(self, db_path="npia_scout.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;") 
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS valid_novels (
                    novel_id INTEGER PRIMARY KEY,
                    title TEXT, author TEXT,
                    fav INTEGER, ep INTEGER, views INTEGER, recs INTEGER,
                    ratio REAL, tags TEXT, 
                    is_19 INTEGER, is_plus INTEGER,
                    url TEXT, last_updated DATETIME
                )
            """)

    def save_novel(self, data):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO valid_novels (
                    novel_id, title, author, fav, ep, views, recs, 
                    ratio, tags, is_19, is_plus, url, last_updated
                ) VALUES (
                    :id, :title, :author, :fav, :ep, :views, :recs, 
                    :ratio, :tags, :is_19, :is_plus, :url, :date
                )
                ON CONFLICT(novel_id) DO UPDATE SET 
                fav=excluded.fav, ep=excluded.ep, views=excluded.views, 
                recs=excluded.recs, ratio=excluded.ratio, tags=excluded.tags, 
                last_updated=excluded.last_updated
            """, data)

    def get_tag_stats(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT tags FROM valid_novels WHERE tags != ''")
            all_tags = []
            for row in cursor.fetchall():
                all_tags.extend([t.strip() for t in row[0].split(',') if t.strip()])
            return Counter(all_tags)
