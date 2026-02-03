# ==========================================
# FILE: core/database.py
# ==========================================
import sqlite3
import os
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name='data/archiver.db'):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.normpath(os.path.join(base_dir, "..", db_name))
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
                    is_completed INTEGER DEFAULT 0,
                    is_19 INTEGER DEFAULT 0,
                    is_plus INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Migration logic for existing databases
            cursor.execute("PRAGMA table_info(novels)")
            cols = [c[1] for c in cursor.fetchall()]
            for col in ['is_completed', 'is_19', 'is_plus']:
                if col not in cols:
                    cursor.execute(f'ALTER TABLE novels ADD COLUMN {col} INTEGER DEFAULT 0')
            
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
                INSERT OR REPLACE INTO novels 
                (id, title, writer, chapters, views, tags_kr, tags_en, url, is_completed, is_19, is_plus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['id'], data['title'], data['writer'], data['chapters'], data['views'],
                ",".join(data['tags_kr']), ",".join(data['tags_en']), data['url'],
                data.get('is_completed', 0), data.get('is_19', 0), data.get('is_plus', 0)
            ))
            conn.commit()

    def blacklist_id(self, novel_id, reason="Filtered"):
        with self._get_connection() as conn:
            conn.execute('INSERT OR IGNORE INTO blacklist (id, reason) VALUES (?, ?)', (novel_id, reason))
            conn.commit()

    def get_all_novels_df(self):
        with self._get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM novels", conn)
            # Revert comma-strings back to lists for filtering
            df['tags_en'] = df['tags_en'].apply(lambda x: x.split(',') if x else [])
            df['tags_kr'] = df['tags_kr'].apply(lambda x: x.split(',') if x else [])
            return df

