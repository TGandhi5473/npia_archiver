# ==========================================
# FILE: core/database.py
# ==========================================
import sqlite3
from datetime import datetime
import streamlit as st

class NovelDB:
    def __init__(self, db_path="npia_encyclopedia.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes tables and high-performance indexes."""
        with sqlite3.connect(self.db_path) as conn:
            # Table 1: The 'Encyclopedia' of Hits
            conn.execute("""
                CREATE TABLE IF NOT EXISTS valid_novels (
                    novel_id INTEGER PRIMARY KEY,
                    title TEXT, author TEXT,
                    fav INTEGER, ep INTEGER, al INTEGER,
                    ratio REAL, tags TEXT, 
                    is_19 INTEGER, is_plus INTEGER,
                    url TEXT, scraped_at DATETIME
                )
            """)
            # Table 2: The Blacklist (Ghost IDs & Low Stats)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    novel_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    scraped_at DATETIME
                )
            """)
            # Index for the 'Sleeper Ratio' to keep the dashboard fast
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ratio ON valid_novels(ratio DESC)")

    def check_exists(self, novel_id):
        """High-speed existence check in both tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM valid_novels WHERE novel_id = ?
                UNION 
                SELECT 1 FROM blacklist WHERE novel_id = ?
            """, (novel_id, novel_id))
            return cursor.fetchone() is not None

    def save_novel(self, data):
        """The 'Writer' logic: Ensures data is physically committed to disk."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO valid_novels 
                    (novel_id, title, author, fav, ep, al, ratio, tags, is_19, is_plus, url, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data['id'], data['title'], data['author'], 
                    data['fav'], data['ep'], data['al'], 
                    data['ratio'], data['tags'], 
                    data['is_19'], data['is_plus'], 
                    data['url'], data['date']
                ))
            return True
        except sqlite3.Error as e:
            print(f"Database Write Error: {e}")
            return False

    def add_to_blacklist(self, novel_id, reason):
        """Locks an ID out so we never waste bandwidth on it again."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO blacklist VALUES (?, ?, ?)",
                (novel_id, reason, datetime.now())
            )
