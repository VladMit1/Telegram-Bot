from database.base import BaseDB
import time 

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
    def set_new_name(self, student_id, new_name):
        query = "UPDATE contacts SET name = ? WHERE id = ?"
        return self.execute(query, (new_name, student_id), commit=True)

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
    
    def delete_student(self, s_id, finance):
        # 1. Проверка долга
        actual_balance = finance.get_actual_balance(s_id)
        if actual_balance < 0:
            return False, f"Должник! Баланс: {actual_balance} PLN. Удаление запрещено."

        # 2. Сбор данных для архива
        student = self.get_by_id(s_id)
        if not student: return False, "Ученик не найден."

        # Считаем итоги
        res_paid = self.execute("SELECT SUM(amount) as total FROM payments WHERE student_id=?", (s_id,), fetchone=True)
        total_paid = res_paid['total'] if res_paid and res_paid['total'] else 0

        res_lessons = self.execute("SELECT COUNT(id) as count FROM lessons WHERE student_id=?", (s_id,), fetchone=True)
        total_lessons = res_lessons['count'] if res_lessons and res_lessons['count'] else 0
        
        # Период (от первого контакта до сегодня)
        period_start = student.get('created_at', 'Неизвестно')
        period_end = time.strftime('%Y-%m-%d %H:%M:%S')

        try:
            # Используем OR REPLACE, чтобы не падать из-за дублей ID в архиве
            self.execute(
                """INSERT OR REPLACE INTO deleted_students 
                    (id, name, phone, total_paid, total_lessons, period_start, period_end) 
                    VALUES (?,?,?,?,?,?,?)""",
                (s_id, student['name'], student['phone'], total_paid, total_lessons, period_start, period_end),
                commit=True
            )

            # Чистим активные таблицы
            self.execute("DELETE FROM lessons WHERE student_id = ?", (s_id,), commit=True)
            self.execute("DELETE FROM payments WHERE student_id = ?", (s_id,), commit=True)
            self.execute("DELETE FROM contacts WHERE id = ?", (s_id,), commit=True)
            
            return True, "Удалено"
        except Exception as e:
            print(f"КРИТИЧЕСКАЯ ОШИБКА БД: {e}") # Это увидишь в консоли
            return False, f"Ошибка БД: {e}"