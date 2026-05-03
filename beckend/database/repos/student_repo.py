from database.base import BaseDB

class StudentRepo(BaseDB):
    def get_all(self):
        return self.execute("SELECT * FROM contacts ORDER BY id ASC", fetchall=True)

    def get_by_id(self, s_id):
        return self.execute("SELECT * FROM contacts WHERE id = ?", (s_id,), fetchone=True)

    def update_balance(self, s_id, amount):
        # УБЕДИСЬ, что тут нет лишних прибавлений
        return self.execute(
            "UPDATE contacts SET balance = balance + ? WHERE id = ?", 
            (amount, s_id), commit=True
        )

    def set_price(self, s_id, price, balance, date):
        return self.execute(
            "UPDATE contacts SET balance = ?, lesson_price = ?, lesson_price_updated_at = ? WHERE id = ?",
            (balance, price, date, s_id), commit=True
        )

    def search(self, query):
        q = f"%{query}%"
        return self.execute(
            "SELECT * FROM contacts WHERE name LIKE ? OR phone LIKE ? OR username LIKE ?",
            (q, q, q), fetchall=True
        )
    def add_contact(self, name, phone, photo_id, chat_id, username=None):
        query = """
            INSERT INTO contacts (name, phone, photo_id, chat_id, username) 
            VALUES (?, ?, ?, ?, ?)
        """
        return self.execute(query, (name, phone, photo_id, chat_id, username), commit=True)

    def set_new_lesson_price(self, student_id, new_price, current_actual_balance):
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = """
            UPDATE contacts 
            SET balance = ?, lesson_price = ?, lesson_price_updated_at = ? 
            WHERE id = ?
        """
        return self.execute(query, (current_actual_balance, new_price, today, student_id), commit=True)

    def try_delete_student(self, student_id, finance):
        """Логика удаления с проверкой баланса"""
        balance = finance.get_actual_balance(student_id)
        
        if balance < 0:
            return False, f"⚠️ Нельзя удалить! У ученика долг: {balance} PLN"
        
        # Если долга нет, удаляем (в идеале здесь нужно удалять и историю уроков/платежей)
        # Для простоты пока удаляем только из contacts
        self.execute("DELETE FROM contacts WHERE id = ?", (student_id,), commit=True)
        return True, "✅ Профиль ученика успешно удален"