import sqlite3
import os
from datetime import datetime

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(base_dir)
        self.db_path = os.path.join(project_root, 'tracker.db')
        self.init_db()

    def init_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS contacts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        phone TEXT UNIQUE, 
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        photo_id TEXT,
                        chat_id INTEGER,
                        last_book TEXT DEFAULT 'Не выбрана',
                        last_page INTEGER DEFAULT 0,
                        balance INTEGER DEFAULT 0
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lessons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        lesson_date DATE,
                        lesson_time TEXT,
                        topic TEXT,
                        duration INTEGER DEFAULT 60,
                        FOREIGN KEY (student_id) REFERENCES contacts (id)
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"Ошибка БД при инициализации: {e}")

    def add_contact(self, name, phone, photo_id, chat_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, phone, photo_id, chat_id) VALUES (?, ?, ?, ?)",
                    (name, phone, photo_id, chat_id)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError: return False
        except: return False

    def get_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id FROM contacts ORDER BY id ASC")
                return cursor.fetchall()
        except: return []

    def search_contacts(self, query):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                search_query = f"%{query}%"
                cursor.execute("""
                    SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id 
                    FROM contacts 
                    WHERE name LIKE ? OR phone LIKE ?
                    ORDER BY id ASC
                """, (search_query, search_query))
                return cursor.fetchall()
        except: return []

    def get_count(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM contacts")
                res = cursor.fetchone()
                return res[0] if res else 0
        except: return 0

    def delete_contact_by_phone(self, phone):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE phone = ?", (phone,))
                conn.commit()
                return True
        except: return False

    # Метод для React API
    def get_contacts_for_api(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM contacts ORDER BY name ASC")
                rows = cursor.fetchall()
                students = []
                for row in rows:
                    cursor.execute("SELECT DISTINCT strftime('%d', lesson_date) FROM lessons WHERE student_id = ?", (row['id'],))
                    days = [int(r[0]) for r in cursor.fetchall()]
                    students.append({**dict(row), "attended_days": days})
                return students
        except: return []

db = DBManager()