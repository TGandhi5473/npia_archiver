# ==========================================
# FILE: core/database.py
# ==========================================
import sqlite3
import os
import pandas as pd

class NovelDB: # Renamed for consistency with your Scraper
    def __init__(self, db_name='data/archiver.db'):
        # Get the absolute path to the project root
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_name)
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Create main table
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

            # 2. Dynamic Migration (Check for missing columns)
            cursor.execute("PRAGMA table_info(novels)")
            existing_cols = [c[1] for c in cursor.fetchall()]
            required_cols = {
                'is_completed': 'INTEGER DEFAULT 0',
                'is_19': 'INTEGER DEFAULT 0',
                'is_plus': 'INTEGER DEFAULT 0',
                'tags_kr': 'TEXT',
                'tags_en': 'TEXT'
            }
            
            for col, definition in required_cols.items():
                if col not in existing_cols:
                    cursor.execute(f'ALTER TABLE novels ADD COLUMN {col} {definition}')
            
            # 3. Create Blacklist table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def is_cached(self, novel_id):
        with self._get_connection() as conn:
            return conn.execute('SELECT 1 FROM novels WHERE id = ?', (novel_id,)).fetchone() is not None

    def save_novel(self, novel_id, data):
        with self._get_connection() as conn:
            conn.execute('''
                INSERT OR REPLACE INTO novels 
                (id, title, writer, chapters, views, tags_kr, tags_en, url, is_completed, is_19, is_plus)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                novel_id, data['title'], data['writer'], data.get('chapters', 0), 
                data.get('views', 0), ",".join(data.get('tags_ko', [])), 
                ",".join(data.get('tags_en', [])), data['url'],
                data.get('is_completed', 0), data.get('is_19', 0), data.get('is_plus', 0)
            ))
            conn.commit()

    def get_all_novels_df(self):
        try:
            with self._get_connection() as conn:
                df = pd.read_sql_query("SELECT * FROM novels", conn)
                if not df.empty:
                    # Conversion with safety check
                    df['tags_en'] = df['tags_en'].apply(lambda x: x.split(',') if x and isinstance(x, str) else [])
                    df['tags_ko'] = df['tags_kr'].apply(lambda x: x.split(',') if x and isinstance(x, str) else [])
                return df
        except Exception:
            return pd.DataFrame()
