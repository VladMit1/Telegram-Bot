import sqlite3

class DBConfigurator:
    @staticmethod
    def setup(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Создание контактов
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

            # Создание уроков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    student_id INTEGER, lesson_date DATE, 
                    lesson_time TEXT, topic TEXT,
                    FOREIGN KEY (student_id) REFERENCES contacts (id)
                )
            ''')

            # Создание платежей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    student_id INTEGER, amount INTEGER, payment_date DATE,
                    FOREIGN KEY (student_id) REFERENCES contacts (id)
                )
            ''')
            #Удаленные контакты (для истории)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deleted_students (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    total_paid INTEGER,
                    total_lessons INTEGER,
                    period_start TEXT,
                    period_end TEXT
                )
            ''')
            conn.commit()
            print("🏗️ Структура БД проверена и готова")