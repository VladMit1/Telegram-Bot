import sqlite3
import os

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.normpath(os.path.join(base_dir, '..', '..', 'tracker.db'))
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_id INTEGER,
                    chat_id INTEGER
                )
            ''')
            conn.commit()

    def add_contact(self, name, phone, message_id, chat_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, phone, message_id, chat_id) VALUES (?, ?, ?, ?)",
                    (name, phone, message_id, chat_id)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def delete_contact_by_phone(self, phone):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE phone = ?", (phone,))
            conn.commit()
            return cursor.rowcount > 0

    def get_all(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone FROM contacts ORDER BY id DESC')
            return cursor.fetchall()

    def get_count(self):
        """Теперь этот метод ПРАВИЛЬНО находится внутри класса"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM contacts")
                result = cursor.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"❌ Ошибка БД: {e}")
            return 0

# Создаем объект БД
db = DBManager()