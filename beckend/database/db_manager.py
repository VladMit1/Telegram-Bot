import sqlite3
import os

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(base_dir))
        self.db_path = os.path.join(project_root, 'tracker.db')
        self.init_db()

    def init_db(self):
        try:
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
        except Exception as e:
            print(f"Ошибка БД при инициализации: {e}")

    def add_contact(self, name, phone, photo_id, chat_id):
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
        except Exception as e:
            print(f"Ошибка при добавлении: {e}")
            return False

    def get_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id FROM contacts ORDER BY id ASC")
                return cursor.fetchall()
        except:
            return []

    # НОВЫЙ МЕТОД ПОИСКА
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
        except:
            return []

    def get_count(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM contacts")
                res = cursor.fetchone()
                return res[0] if res else 0
        except:
            return 0

    def delete_contact_by_phone(self, phone):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE phone = ?", (phone,))
                conn.commit()
                return True
        except:
            return False

db = DBManager()