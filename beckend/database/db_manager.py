import sqlite3
import os
import requests
from datetime import datetime, timedelta

def round_time_to_hour(dt=None):
    if dt is None:
        dt = datetime.now()
    step = 60 
    accumulated_minutes = dt.minute + dt.second / 60
    if accumulated_minutes >= (step / 2):
        rounded_dt = dt.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=step)
    else:
        rounded_dt = dt.replace(minute=0, second=0, microsecond=0)
    return rounded_dt.strftime("%Y-%m-%d"), rounded_dt.strftime("%H:%M")

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
                
                # 1. Основная таблица
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
                        lesson_price INTEGER DEFAULT 50,
                        lesson_price_updated_at TIMESTAMP DEFAULT '2024-01-01 00:00:00',
                        username TEXT
                    )
                ''')

                # 2. Миграции
                cursor.execute("PRAGMA table_info(contacts)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                required_migrations = [
                    ('username', 'TEXT'),
                    ('lesson_price', 'INTEGER DEFAULT 50'),
                    ('lesson_price_updated_at', 'TIMESTAMP'),
                    ('last_book', "TEXT DEFAULT 'Не выбрана'"),
                    ('last_page', "INTEGER DEFAULT 0"),
                    ('balance', "INTEGER DEFAULT 0")
                ]
                for col_name, col_type in required_migrations:
                    if col_name not in existing_columns:
                        cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col_name} {col_type}")

                # 3. Связанные таблицы
                cursor.execute('''CREATE TABLE IF NOT EXISTS lessons (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, lesson_date DATE, lesson_time TEXT, topic TEXT, duration INTEGER, FOREIGN KEY (student_id) REFERENCES contacts (id))''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER, amount INTEGER, payment_date DATE, FOREIGN KEY (student_id) REFERENCES contacts (id))''')
                cursor.execute('''CREATE TABLE IF NOT EXISTS deleted_contacts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, total_paid INTEGER, total_lessons INTEGER, period_start TEXT, period_end TEXT)''')
                
                conn.commit()
                print("✅ БД инициализирована")
        except Exception as e:
            print(f"❌ Ошибка БД: {e}")

    # --- Методы для работы с контактами ---
    def add_contact(self, name, phone, photo_id, chat_id, username=None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO contacts (name, phone, photo_id, chat_id, username) VALUES (?, ?, ?, ?, ?)", (name, phone, photo_id, chat_id, username))
                conn.commit()
                return True
        except: return False

    def get_all(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id, chat_id, last_book, last_page, balance, lesson_price, username FROM contacts ORDER BY id ASC")
                return cursor.fetchall()
        except: return []

    def get_student_by_id(self, student_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM contacts WHERE id = ?", (student_id,))
                return cursor.fetchone()
        except: return None

    # --- ТЕ САМЫЕ МЕТОДЫ ДЛЯ КАЛЕНДАРЯ ---
    def get_busy_days(self, student_id, year, month):
        """Дни занятий конкретного ученика (нужен для календаря в режиме view)"""
        month_str = f"{year}-{str(month).zfill(2)}%"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT lesson_date FROM lessons WHERE student_id = ? AND lesson_date LIKE ?", (student_id, month_str))
                return [int(row[0].split('-')[2]) for row in cursor.fetchall()]
        except: return []

    def get_all_busy_days(self, year, month):
        """Дни занятий ВСЕХ учеников (нужен для админ-календаря 'all')"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT strftime('%d', lesson_date) FROM lessons WHERE strftime('%Y', lesson_date) = ? AND strftime('%m', lesson_date) = ?", (str(year), f"{month:02d}"))
                return [int(row[0]) for row in cursor.fetchall()]
        except: return []

    def get_payment_dates(self, student_id):
        """Даты платежей (нужен для render_pay_pad)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT payment_date FROM payments WHERE student_id = ?", (student_id,))
                return [row[0] for row in cursor.fetchall()] # Вернет список ['2026-05-02', ...]
        except: return []

    # --- Управление уроками ---
    def add_lesson(self, student_id, date, time, topic="Урок", duration=60):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO lessons (student_id, lesson_date, lesson_time, topic, duration) VALUES (?, ?, ?, ?, ?)", (student_id, date, time, topic, duration))
                conn.commit()
                return cursor.lastrowid
        except: return None

    def delete_lesson(self, lesson_date, lesson_time, student_id):
        """Удаляет занятие по дате/времени и возвращает стоимость на баланс"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Сначала находим цену урока для этого конкретного студента
                cursor.execute("SELECT lesson_price FROM contacts WHERE id = ?", (student_id,))
                price_row = cursor.fetchone()
                price = price_row[0] if price_row else 50

                # 2. Удаляем сам урок
                cursor.execute("""
                    DELETE FROM lessons 
                    WHERE lesson_date = ? AND lesson_time = ? AND student_id = ?
                """, (lesson_date, lesson_time, student_id))
                
                # Если что-то удалили (rowcount > 0), возвращаем деньги на баланс
                if cursor.rowcount > 0:
                    cursor.execute("UPDATE contacts SET balance = balance + ? WHERE id = ?", (price, student_id))
                    conn.commit()
                    return True
                return False
        except Exception as e:
            print(f"❌ Ошибка при удалении урока: {e}")
            return False
    def get_booked_details(self, date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT l.lesson_time, l.student_id, c.name FROM lessons l JOIN contacts c ON l.student_id = c.id WHERE l.lesson_date = ?", (date,))
                return {row[0]: {'id': row[1], 'name': row[2]} for row in cursor.fetchall()}
        except: return {}

    def get_lesson_id(self, date, time, student_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM lessons WHERE lesson_date = ? AND lesson_time = ? AND student_id = ?", (date, time, student_id))
                res = cursor.fetchone()
                return res[0] if res else None
        except: return None

    # --- Финансы ---
    def add_payment(self, student_id, amount, payment_date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO payments (student_id, amount, payment_date) VALUES (?, ?, ?)", (student_id, amount, payment_date))
                cursor.execute("UPDATE contacts SET balance = balance + ? WHERE id = ?", (amount, student_id))
                conn.commit()
        except: pass

    def delete_payment(self, payment_id, student_id, amount):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
                cursor.execute("UPDATE contacts SET balance = balance - ? WHERE id = ?", (amount, student_id))
                conn.commit()
                return True
        except: return False

    def set_new_lesson_price(self, student_id, new_price, current_actual_balance):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE contacts SET balance = ?, lesson_price = ?, lesson_price_updated_at = ? WHERE id = ?", (current_actual_balance, new_price, today, student_id))
                conn.commit()
                return True
        except: return False

    # --- Остальные методы ---
    def universal_update_contact(self, student_id, update_data):
        if not update_data: return False
        keys = update_data.keys()
        set_clause = ", ".join([f"{key} = ?" for key in keys])
        values = list(update_data.values()) + [student_id]
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE contacts SET {set_clause} WHERE id = ?", values)
                conn.commit()
                return True
        except: return False

    def search_contacts(self, query):
        search_query = f"%{query}%"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, phone, strftime('%d.%m.%Y', created_at), photo_id, chat_id, last_book, last_page, balance, lesson_price, username FROM contacts WHERE name LIKE ? OR phone LIKE ? OR username LIKE ? ORDER BY id ASC", (search_query, search_query, search_query))
                return cursor.fetchall()
        except: return []

db = DBManager()