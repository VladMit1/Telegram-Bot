import sqlite3

class DBManager:
    def __init__(self, db_path='tracker.db'):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_db()

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

    def add_contact(self, name, time, phone=None):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO contacts (name, time, phone) VALUES (?, ?, ?)', (name, time, phone))
        self.conn.commit()

    def get_all_contacts(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT name, phone, time, calls_count FROM contacts ORDER BY id DESC')
        rows = cursor.fetchall()
        return [{"name": r[0], "phone": r[1], "time": r[2], "calls": r[3]} for r in rows]

# Создаем один экземпляр для всего приложения
db = DBManager()