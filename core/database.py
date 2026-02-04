import sqlite3
from datetime import datetime

class NovelDB:
    def __init__(self, db_path="npia_scout.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        """Initializes tables and high-speed indexes."""
        with self.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS valid_novels (
                    novel_id INTEGER PRIMARY KEY,
                    title TEXT, author TEXT,
                    fav INTEGER, ep INTEGER, al INTEGER,
                    ratio REAL, tags TEXT, 
                    is_19 INTEGER, is_plus INTEGER,
                    url TEXT, last_updated DATETIME
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    novel_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    scraped_at DATETIME
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ratio ON valid_novels(ratio DESC)")

    def check_exists(self, novel_id):
        """Fast existence check across both hit and miss tables."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM valid_novels WHERE novel_id = ?
                UNION SELECT 1 FROM blacklist WHERE novel_id = ?
            """, (novel_id, novel_id))
            return cursor.fetchone() is not None

    def save_novel(self, data):
        """Atomic UPSERT: Updates stats if novel exists, inserts if new."""
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO valid_novels (novel_id, title, author, fav, ep, al, ratio, tags, is_19, is_plus, url, last_updated)
                    VALUES (:id, :title, :author, :fav, :ep, :al, :ratio, :tags, :is_19, :is_plus, :url, :date)
                    ON CONFLICT(novel_id) DO UPDATE SET
                        fav=excluded.fav, ep=excluded.ep, al=excluded.al, 
                        ratio=excluded.ratio, last_updated=excluded.last_updated
                """, data)
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False

    def add_to_blacklist(self, novel_id, reason):
        with self.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO blacklist VALUES (?, ?, ?)", 
                         (novel_id, reason, datetime.now()))
