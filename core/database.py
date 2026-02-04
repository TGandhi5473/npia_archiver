import sqlite3
from datetime import datetime

class NovelDB:
    def __init__(self, db_path="npia_scout.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        # We use a 30s timeout and WAL mode to handle concurrent read/writes
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;") 
        return conn

    def _init_db(self):
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
                    reason TEXT, scraped_at DATETIME
                )
            """)

    def check_exists(self, novel_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM (
                    SELECT novel_id FROM valid_novels WHERE novel_id = ?
                    UNION ALL 
                    SELECT novel_id FROM blacklist WHERE novel_id = ?
                ) LIMIT 1
            """, (novel_id, novel_id))
            return cursor.fetchone() is not None

    def save_novel(self, data):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO valid_novels VALUES 
                (:id, :title, :author, :fav, :ep, :al, :ratio, :tags, :is_19, :is_plus, :url, :date)
                ON CONFLICT(novel_id) DO UPDATE SET 
                fav=excluded.fav, ep=excluded.ep, ratio=excluded.ratio, last_updated=excluded.last_updated
            """, data)

    def add_to_blacklist(self, novel_id, reason):
        with self.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO blacklist VALUES (?, ?, ?)", 
                         (novel_id, reason, datetime.now()))

    def clear_vault(self):
        """Wipes data and reclaims space. Fixes the VACUUM transaction error."""
        conn = self.get_connection()
        try:
            # VITAL: Set isolation_level to None for Autocommit mode.
            # VACUUM cannot run inside a standard BEGIN/COMMIT block.
            conn.isolation_level = None 
            cursor = conn.cursor()
            cursor.execute("DELETE FROM valid_novels")
            cursor.execute("VACUUM")
            return True
        except Exception as e:
            print(f"Clear error: {e}")
            return False
        finally:
            conn.close()
