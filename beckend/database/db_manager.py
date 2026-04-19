import sqlite3
import os
import requests
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
                        balance INTEGER DEFAULT 0,
                        total_paid INTEGER DEFAULT 0,
                        lesson_price INTEGER DEFAULT 500,
                        username TEXT  -- ИЗМЕНЕНО: добавлено поле при создании
                    )
                ''')

                cursor.execute("PRAGMA table_info(contacts)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                
                # ИЗМЕНЕНО: Авто-миграция для username
                if 'username' not in existing_columns:
                    print("🛠 Добавляю колонку username в таблицу contacts...")
                    cursor.execute("ALTER TABLE contacts ADD COLUMN username TEXT")

                if 'total_paid' not in existing_columns:
                    cursor.execute("ALTER TABLE contacts ADD COLUMN total_paid INTEGER DEFAULT 0")
                
                if 'lesson_price' not in existing_columns:
                    cursor.execute("ALTER TABLE contacts ADD COLUMN lesson_price INTEGER DEFAULT 500")

                # (Остальные CREATE TABLE остаются без изменений)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS lessons (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        lesson_date DATE,
                        lesson_time TEXT,
                        topic TEXT,
                        duration INTEGER,
                        FOREIGN KEY (student_id) REFERENCES contacts (id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS payments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        student_id INTEGER,
                        amount INTEGER,
                        payment_date DATE,
                        FOREIGN KEY (student_id) REFERENCES contacts (id)
                    )
                ''')
                conn.commit()
                print("✅ База данных успешно инициализирована")
        except Exception as e:
            print(f"❌ Ошибка БД при инициализации: {e}")

    def add_contact(self, name, phone, photo_id, chat_id, username=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO contacts (name, phone, photo_id, chat_id, username) VALUES (?, ?, ?, ?, ?)",
                    (name, phone, photo_id, chat_id, username)
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError: return False
        except: return False

    def get_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Мы берем id, name, phone, date, photo_id, и в конце добавляем все остальные поля для корректного индекса (11)
                cursor.execute("""
                    SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id, 
                           chat_id, last_book, last_page, balance, total_paid, lesson_price, username 
                    FROM contacts ORDER BY id ASC
                """)
                return cursor.fetchall()
        except: return []

    def search_contacts(self, query):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                search_query = f"%{query}%"
                cursor.execute("""
                    SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id,
                           chat_id, last_book, last_page, balance, total_paid, lesson_price, username
                    FROM contacts 
                    WHERE name LIKE ? OR phone LIKE ? OR username LIKE ?
                    ORDER BY id ASC
                """, (search_query, search_query, search_query))
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
    def get_contacts_for_api(self, bot_token):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM contacts ORDER BY name ASC")
                rows = cursor.fetchall()
                
                students = []
                for row in rows:
                    photo_url = None
                    photo_id = row['photo_id']
                    
                    if photo_id:
                        try:
                            url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={photo_id}"
                            file_info = requests.get(url).json()
                            if file_info.get('ok'):
                                file_path = file_info['result']['file_path']
                                photo_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                        except: pass

                    cursor.execute("SELECT DISTINCT lesson_date FROM lessons WHERE student_id = ?", (row['id'],))
                    lesson_dates = [r[0] for r in cursor.fetchall()]

                    cursor.execute("SELECT id,amount, payment_date FROM payments WHERE student_id = ?", (row['id'],))
                    payments = [dict(p) for p in cursor.fetchall()]

                    student_dict = dict(row)
                    student_dict['photo_url'] = photo_url
                    student_dict['attended_lessons'] = lesson_dates
                    student_dict['payments'] = payments
                    students.append(student_dict)
                return students
        except Exception as e:
            print(f"Ошибка API: {e}")
            return []
    def universal_update_contact(self, student_id, update_data):
        try:
            if not update_data: return False
            keys = update_data.keys()
            set_clause = ", ".join([f"{key} = ?" for key in keys])
            values = list(update_data.values()) + [student_id]
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE contacts SET {set_clause} WHERE id = ?", values)
                conn.commit()
                return True
        except: return False
    def add_lesson(self, student_id, date, time, topic, duration):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO lessons (student_id, lesson_date, lesson_time, topic, duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, date, time, topic, duration))
                conn.commit()
                return cursor.lastrowid # Возвращаем ID нового урока
        except sqlite3.Error as e:
            print(f"Ошибка БД: {e}")
            return NoneS
    def get_all_lessons(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
        # Тянем всё из уроков + имя из контактов
            cursor.execute('''
                SELECT lessons.*, contacts.name as student_name 
                FROM lessons 
                JOIN contacts ON lessons.student_id = contacts.id
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def update_lesson(self, lesson_id, update_data):
        try:
            if not update_data:
                return False
                
            keys = update_data.keys()
            set_clause = ", ".join([f"{key} = ?" for key in keys])
            values = list(update_data.values())
            values.append(lesson_id)

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = f"UPDATE lessons SET {set_clause} WHERE id = ?"
                cursor.execute(query, values)
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при обновлении занятия {lesson_id}: {e}")
            return False
            
    def delete_lesson(self, lesson_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
                conn.commit()
                # Возвращаем True, если хотя бы одна строка была удалена
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при удалении занятия {lesson_id}: {e}")
            return False
    def add_payment(self, student_id, amount, date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Записываем платеж
                cursor.execute("INSERT INTO payments (student_id, amount, payment_date) VALUES (?, ?, ?)", (student_id, amount, date))
                # 2. Обновляем общий счетчик в контактах
                cursor.execute("UPDATE contacts SET total_paid = total_paid + ? WHERE id = ?", (amount, student_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка при записи платежа: {e}")
            return False
    def delete_payment(self, payment_id, student_id, amount):
        print(f"Удаление платежа ID {payment_id} для студента {student_id} на сумму {amount}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Удаляем сам платеж
                cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
                # 2. Вычитаем сумму из общего баланса студента
                cursor.execute(
                    "UPDATE contacts SET total_paid = total_paid - ? WHERE id = ?",
                    (amount, student_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка удаления платежа: {e}")
            return False
        
    def get_student_by_phone(self, phone):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id 
                    FROM contacts WHERE phone = ?
                """, (phone,))
                return cursor.fetchone()
        except: return None
db = DBManager()