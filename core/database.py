import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path='data/archiver.db'):
        # Get absolute path to ensure it works anywhere
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, "..", db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        """Creates tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Main Archive Table
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
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def save_novel(self, data):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO novels (id, title, writer, chapters, views, tags_kr, tags_en, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['id'], data['title'], data['writer'], data['chapters'], 
                data['views'], ",".join(data['tags_kr']), ",".join(data['tags_en']), data['url']
            ))
            conn.commit()

    def is_blacklisted(self, novel_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM blacklist WHERE id = ?', (novel_id,))
            return cursor.fetchone() is not None

    def blacklist_id(self, novel_id, reason="Filtered"):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO blacklist (id, reason) VALUES (?, ?)', (novel_id, reason))
            conn.commit()
