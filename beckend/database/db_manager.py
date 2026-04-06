import sqlite3
import os

class DBManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.normpath(os.path.join(base_dir, '..', '..', 'tracker.db'))
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                phone TEXT UNIQUE, 
                time TEXT,
                calls_count INTEGER DEFAULT 0,
                message_id INTEGER,
                chat_id INTEGER
            )
        ''')
        self.conn.commit()

    def add_contact(self, name, phone, message_id, chat_id):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO contacts (name, phone, time, message_id, chat_id) VALUES (?, ?, ?, ?, ?)",
                (name, phone, "12:00", message_id, chat_id)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_contact_info(self, contact_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT message_id, chat_id FROM contacts WHERE id = ?", (contact_id,))
        return cursor.fetchone()

    def delete_contact(self, contact_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        self.conn.commit()

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, name, phone, time, calls_count FROM contacts ORDER BY id DESC')
        return cursor.fetchall()

db = DBManager()