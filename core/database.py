import sqlite3
from datetime import datetime

class NovelDB:
    def __init__(self, db_path="npia_scout.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self):
        """
        Creates a thread-safe connection with a high timeout to 
        prevent 'database is locked' errors during heavy scraping.
        """
        conn = sqlite3.connect(
            self.db_path, 
            check_same_thread=False,
            timeout=30.0  # Wait up to 30s for other writes to finish
        )
        # Enable WAL mode for better read/write concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            # Main novel storage
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
            # Blacklist for ghosts and low-stat novels
            conn.execute("""
                CREATE TABLE IF NOT EXISTS blacklist (
                    novel_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    scraped_at DATETIME
                )
            """)
            # Index for fast sorting by ratio in the UI
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ratio ON valid_novels(ratio DESC)")

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
        """
        Atomic UPSERT: Updates stats if novel exists, inserts if new.
        Uses the 'excluded' keyword to update existing records with fresh stats.
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO valid_novels (
                        novel_id, title, author, fav, ep, al, 
                        ratio, tags, is_19, is_plus, url, last_updated
                    )
                    VALUES (:id, :title, :author, :fav, :ep, :al, 
                            :ratio, :tags, :is_19, :is_plus, :url, :date)
                    ON CONFLICT(novel_id) DO UPDATE SET
                        fav=excluded.fav, 
                        ep=excluded.ep, 
                        al=excluded.al, 
                        ratio=excluded.ratio, 
                        last_updated=excluded.last_updated
                """, data)
            return True
        except Exception as e:
            print(f"DB Error on ID {data.get('id')}: {e}")
            return False

    def add_to_blacklist(self, novel_id, reason):
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO blacklist (novel_id, reason, scraped_at) 
                VALUES (?, ?, ?)
            """, (novel_id, reason, datetime.now()))
