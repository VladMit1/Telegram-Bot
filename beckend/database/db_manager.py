import sqlite3
import os

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(base_dir))
        self.db_path = os.path.join(project_root, 'tracker.db')
        
        # Печатаем путь, чтобы вы точно видели, где создается файл
        print(f"📂 База данных: {self.db_path}")
        self.init_db()

    def init_db(self):
        """Создает таблицу contacts, если её нет"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    phone TEXT UNIQUE, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    photo_id TEXT,
                    chat_id INTEGER
                )
            ''')
            conn.commit()
    def add_contact(self, name, phone, photo_id, chat_id):
        # Добавим вызов init_db прямо сюда на случай, если файл был удален
        self.init_db() 
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, phone, photo_id, chat_id) VALUES (?, ?, ?, ?)",
                    (name, phone, photo_id, chat_id)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
        except sqlite3.OperationalError as e:
            print(f"⚠️ Критическая ошибка БД: {e}")
            return False
    def get_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Поменял DESC на ASC, чтобы новые были в конце (внизу чата)
                cursor.execute('''
                    SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id 
                    FROM contacts ORDER BY id ASC
                ''')
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка get_all: {e}")
            return []

    def search_contacts(self, query):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                search_term = f"%{query}%"
                cursor.execute('''
                    SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id 
                    FROM contacts WHERE name LIKE ? OR phone LIKE ? ORDER BY id ASC
                ''', (search_term, search_term))
                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return []

    def delete_contact_by_phone(self, phone):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE phone = ?", (phone,))
            conn.commit()
            return cursor.rowcount > 0

    def get_count(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM contacts")
                res = cursor.fetchone()
                return res[0] if res else 0
        except Exception:
            return 0

db = DBManager()