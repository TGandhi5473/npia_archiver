import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_name='data/archiver.db'):
        # Dynamic pathing: finds the /data folder relative to this file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.normpath(os.path.join(base_dir, "..", db_name))
        
        # Ensure data folder exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Builds the tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Novels Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS novels (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    writer TEXT,
                    chapters INTEGER,
                    views INTEGER,
                    tags_kr TEXT,
                    tags_en TEXT,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Blacklist Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def is_archived(self, novel_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT 1 FROM novels WHERE id = ?', (novel_id,)).fetchone() is not None

    def is_blacklisted(self, novel_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT 1 FROM blacklist WHERE id = ?', (novel_id,)).fetchone() is not None

    def save_novel(self, data):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO novels (id, title, writer, chapters, views, tags_kr, tags_en, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['id'], data['title'], data['writer'], data['chapters'], 
                data['views'], ",".join(data['tags_kr']), ",".join(data['tags_en']), data['url']
            ))
            conn.commit()

    def blacklist_id(self, novel_id, reason="Filtered"):
        with self._get_connection() as conn:
            conn.execute('INSERT OR IGNORE INTO blacklist (id, reason) VALUES (?, ?)', (novel_id, reason))
            conn.commit()
