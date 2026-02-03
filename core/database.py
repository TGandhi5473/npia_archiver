# ==========================================
# FILE: core/database.py
# ==========================================
import sqlite3
import os
import pandas as pd

class NovelDB:
    def __init__(self, db_name='data/archiver.db'):
        # Simple absolute path relative to the script location
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_name)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS novels (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    writer TEXT,
                    chapters INTEGER,
                    views INTEGER,
                    tags_kr TEXT,
                    tags_en TEXT,
                    url TEXT,
                    is_completed INTEGER DEFAULT 0,
                    is_19 INTEGER DEFAULT 0,
                    is_plus INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def is_cached(self, novel_id):
        """Checks if ID exists in the local database."""
        with self._get_connection() as conn:
            res = conn.execute('SELECT 1 FROM novels WHERE id = ?', (novel_id,)).fetchone()
            return res is not None

    def save_novel(self, novel_id, data):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO novels 
                (id, title, writer, chapters, views, tags_kr, tags_en, url, is_completed, is_19, is_plus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                novel_id, data['title'], data['writer'], data['chapters'], data['views'],
                ",".join(data['tags_ko']), ",".join(data['tags_en']), data['url'],
                data['is_completed'], data['is_19'], data['is_plus']
            ))
            conn.commit()

    def get_all_novels_df(self):
        with self._get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM novels", conn)
            # Revert comma-strings back to lists for the UI
            if not df.empty:
                df['tags_en'] = df['tags_en'].apply(lambda x: x.split(',') if x else [])
            return df
