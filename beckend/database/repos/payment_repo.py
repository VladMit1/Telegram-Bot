from database.base import BaseDB

class PaymentRepo(BaseDB):
    def add(self, s_id, amount, date, student_repo):
        # ТОЛЬКО запись в историю. Баланс в контактах НЕ ТРОГАЕМ.
        return self.execute(
            "INSERT INTO payments (student_id, amount, payment_date) VALUES (?, ?, ?)",
            (s_id, amount, date), commit=True
        )
    def get_dates_by_student(self, s_id):
        """Возвращает список дат всех платежей ученика"""
        rows = self.execute(
            "SELECT DISTINCT payment_date FROM payments WHERE student_id = ?",
            (s_id,), fetchall=True
        )
    
        # Если rows пришел как int (ошибка в execute) или None, возвращаем пустой список
        if not isinstance(rows, list):
            return []
        
    # Извлекаем данные через имя колонки ['payment_date']
        return [row['payment_date'] for row in rows]



    def delete(self, p_id):
        """Удаляет запись о платеже по его ID"""
        return self.execute(
            "DELETE FROM payments WHERE id = ?", 
            (p_id,), 
            commit=True
        )