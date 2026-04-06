import sqlite3
import os

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # База лежит в корневой папке проекта
        db_path = os.path.normpath(os.path.join(base_dir, '..', 'tracker.db'))
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_db()
        print(f"🗄️ База подключена: {db_path}")

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT,
                time TEXT,
                calls_count INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    def add_contact(self, name, time, phone):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (name, phone, time, calls_count) VALUES (?, ?, ?, ?)",
            (name, phone, time, 0)
        )
        self.conn.commit()
        print(f"✅ Контакт сохранен в БД: {name}")

    def get_all_contacts(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, phone, time, calls_count FROM contacts ORDER BY id DESC')
        rows = cursor.fetchall()
        return [
            {"id": r[0], "name": r[1], "phone": r[2], "time": r[3], "calls": r[4]} 
            for r in rows
        ]

db = DBManager()