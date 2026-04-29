import sqlite3
import os
import requests
from datetime import datetime

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
                
                # 1. Создаем основную таблицу, если её вообще нет
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

                # 2. ПОЛНАЯ ПРОВЕРКА КОЛОНОК (Миграция)
                # Это нужно, чтобы код не падал на разных компах
                cursor.execute("PRAGMA table_info(contacts)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                
                # Список того, что ДОЛЖНО быть в таблице
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
                        print(f"🛠 Миграция: Добавляю отсутствующую колонку {col_name}...")
                        cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col_name} {col_type}")

                # 3. Создаем связанные таблицы
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
                print("✅ База данных полностью инициализирована и проверена")
        except Exception as e:
            print(f"❌ Ошибка БД при инициализации: {e}")
    def execute_query(self, query, params=()):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return False
    def add_contact(self, name, phone, photo_id, chat_id, username=None):
        try:
            if not username and "@" in name:
                parts = name.split()
                # Находим слово с @
                un = next((w for w in parts if w.startswith("@")), None)
                if un:
                    username = un
                    # Убираем ник из имени
                    name = " ".join([w for w in parts if w != un]).strip()
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
                           chat_id, last_book, last_page, balance, lesson_price, username 
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
                           chat_id, last_book, last_page, balance, lesson_price, username
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
    def try_delete_student(self, student_id, finance):
        try:
            # 1. Проверяем баланс перед удалением
            balance = finance.get_actual_balance(student_id)
        
            if balance < 0:
                # Если есть долг, возвращаем False и текст ошибки
                return False, f"Нельзя удалить! У ученика долг: {balance} PLN. Сначала закройте долг."

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 2. Собираем статистику для таблицы deleted_contacts
                cursor.execute("SELECT name, phone, date_added FROM contacts WHERE id = ?", (student_id,))
                student = cursor.fetchone()

                if student:
                    name, phone, date_added = student

                    # Считаем итого по деньгам и урокам
                    cursor.execute("SELECT SUM(amount) FROM payments WHERE student_id = ?", (student_id,))
                    total_paid = cursor.fetchone()[0] or 0

                    cursor.execute("SELECT COUNT(*) FROM lessons WHERE student_id = ?", (student_id,))
                    total_lessons = cursor.fetchone()[0] or 0

                    # 3. Сохраняем в архив (таблицу deleted_contacts создай заранее)
                    cursor.execute("""
                        INSERT INTO deleted_contacts 
                        (name, phone, total_paid, total_lessons, period_start, period_end)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, phone, total_paid, total_lessons, date_added, datetime.now().strftime("%Y-%m-%d")))

                # 4. Полная зачистка оперативных данных
                cursor.execute("DELETE FROM payments WHERE student_id = ?", (student_id,))
                cursor.execute("DELETE FROM lessons WHERE student_id = ?", (student_id,))
                cursor.execute("DELETE FROM contacts WHERE id = ?", (student_id,))

                conn.commit()
                return True, "Ученик успешно удален и заархивирован."

        except Exception as e:
            print(f"Ошибка удаления: {e}")
            return False, f"Ошибка базы данных: {e}"

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
    def add_lesson(self, student_id, date, time, topic="Урок", duration=60):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Просто добавляем урок. Никаких UPDATE баланса!
                cursor.execute('''
                    INSERT INTO lessons (student_id, lesson_date, lesson_time, topic, duration)
                    VALUES (?, ?, ?, ?, ?)
                ''', (student_id, date, time, topic, duration))
            
                conn.commit()
                return cursor.lastrowid 
        except sqlite3.Error as e:
            print(f"❌ Ошибка БД при добавлении урока: {e}")
        return None
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
                # 2. СПИСЫВАЕМ ДЕНЬГИ
                # Мы вычитаем lesson_price из balance
                cursor.execute("""
                    UPDATE contacts 
                    SET balance = balance + lesson_price 
                    WHERE id IN (
                        SELECT student_id FROM lessons WHERE id = ?
                    )
                """, (lesson_id,))
                conn.commit()
                # Возвращаем True, если хотя бы одна строка была удалена
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Ошибка при удалении занятия {lesson_id}: {e}")
            return False
    def add_payment(self, student_id, amount, payment_date):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Используем правильное имя колонки payment_date из твоего  PRAGMA
                cursor.execute("""
                    INSERT INTO payments (student_id, amount, payment_date) 
                    VALUES (?, ?, ?)
                """, (student_id, amount, payment_date))

                # Сразу обновляем баланс в таблице contacts (опционально,   если ты его там хранишь)
                cursor.execute("""
                    UPDATE contacts SET balance = balance + ? WHERE id = ?
                """, (amount, student_id))

                conn.commit()
        except Exception as e:
            print(f"Ошибка при записи платежа: {e}")
    def delete_payment(self, payment_id, student_id, amount):
        print(f"Удаление платежа ID {payment_id} для студента {student_id} на сумму {amount}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Удаляем сам платеж
                cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
                # 2. Вычитаем сумму из общего баланса студента
                cursor.execute(
                    "UPDATE contacts SET balance = balance - ? WHERE id = ?",
                    (amount, student_id)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка удаления платежа: {e}")
            return False
        
    def get_student_by_id(self, student_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM contacts WHERE id = ?", (student_id,))
                return cursor.fetchone()
        except: return None

    def get_busy_days(self, student_id, year, month):
    # Формируем строку месяца для поиска "YYYY-MM"
        month_str = f"{year}-{str(month).zfill(2)}%"
        query = "SELECT DISTINCT lesson_date FROM lessons WHERE student_id  = ? AND lesson_date LIKE ?"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (student_id, month_str))
                # Получаем список дат и вытаскиваем только день (последние  две цифры)
                results = cursor.fetchall()
                return [int(row[0].split('-')[2]) for row in results]
        except:
            return []
        
    def get_booked_times(self, student_id, date_str):
        """Возвращает список забронированных времен (строки типа '09:00')"""
        query = "SELECT lesson_time FROM lessons WHERE student_id = ? AND   lesson_date = ?"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (student_id, date_str))
                results = cursor.fetchall()
                return [row[0] for row in results] # Получим список     ['09:00', '14:00']
        except:
            return []
        
    def get_booked_times_with_names(self, date_str):
        """Возвращает словарь вида {'09:00': 'Имя Ученика', '11:00': 'Другой    Ученик'}"""
        query = """
            SELECT l.lesson_time, c.name 
            FROM lessons l
            JOIN contacts c ON l.student_id = c.id
            WHERE l.lesson_date = ?
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (date_str,))
                results = cursor.fetchall()
                # Превращаем список кортежей в удобный словарь
                return {row[0]: row[1] for row in results}
        except Exception as e:
            print(f"Ошибка получения расписания: {e}")
            return {}
    def get_payment_dates(self, student_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Выбираем даты из колонки payment_date
                cursor.execute("SELECT DISTINCT payment_date FROM payments  WHERE student_id = ?", (student_id,))
                return [row[0] for row in cursor.fetchall()]
        except:
            return []
    def get_all_busy_days(self, year, month):
    # Используем strftime для фильтрации по году и месяцу
        query = """
            SELECT DISTINCT strftime('%d', lesson_date) 
            FROM lessons 
            WHERE strftime('%Y', lesson_date) = ? 
            AND strftime('%m', lesson_date) = ?
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Важно: sqlite ожидает строки в параметрах для strftime
                cursor.execute(query, (str(year), f"{month:02d}"))
                results = cursor.fetchall()
                # Извлекаем первый элемент каждого кортежа и превращаем в число
                return [int(row[0]) for row in results]
        except Exception as e:
            print(f"Ошибка в get_all_busy_days: {e}")
            return []
    def set_new_lesson_price(self, student_id, new_price, current_actual_balance):
    # Используем текущее время для отметки маяка
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE contacts 
                    SET balance = ?, 
                        lesson_price = ?, 
                        lesson_price_updated_at = ? 
                    WHERE id = ?
                """, (current_actual_balance, new_price, today, student_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка в set_new_lesson_price: {e}")
            return False
    def auto_lesson_check_in(self, student_id):
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:00")

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 1. Проверяем занятость времени
                check_query = "SELECT student_id FROM lessons WHERE lesson_date = ? AND lesson_time = ?"
                cursor.execute(check_query, (current_date, current_time))
                row = cursor.fetchone()

                if row:
                    found_id = row[0]
                    # Если это тот же самый ученик — пропускаем к уроку
                    if str(found_id) == str(student_id):
                        return True, current_time
                    
                    # Если ID другой — вытаскиваем имя из таблицы CONTACTS
                    try:
                        cursor.execute("SELECT name FROM contacts WHERE id = ?", (found_id,))
                        res_name = cursor.fetchone()
                        busy_name = res_name[0] if res_name else f"ID:{found_id}"
                    except:
                        busy_name = "другим учеником"
                    
                    return False, busy_name

                # 2. Если время свободно — создаем запись
                # Добавил duration=60, так как в твоей PRAGMA это поле есть
                cursor.execute("""
                    INSERT INTO lessons (student_id, lesson_date, lesson_time, topic, duration)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_id, current_date, current_time, "Авто-урок", 60))
                conn.commit()
                
                return True, current_time

        except Exception as e:
            print(f"❌ Ошибка БД: {e}")
            return False, f"Ошибка базы: {str(e)}"
db = DBManager()