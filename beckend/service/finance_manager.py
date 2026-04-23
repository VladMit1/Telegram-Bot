import sqlite3
from datetime import datetime

class FinanceManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_today(self):
        # Получаем дату в формате ГГГГ-ММ-ДД по местному времени
        return datetime.now().strftime('%Y-%m-%d')

    def get_actual_balance(self, student_id):
        today = self._get_today()
        query = """
        SELECT 
            (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE student_id = ?) -
            (SELECT COALESCE(COUNT(*), 0) * c.lesson_price 
             FROM lessons l 
             JOIN contacts c ON l.student_id = c.id 
             WHERE l.student_id = ? AND l.lesson_date <= ?)
        FROM contacts c
        WHERE c.id = ?
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Передаем today третьим параметром
                cursor.execute(query, (student_id, student_id, today, student_id))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else 0
        except Exception as e:
            print(f"❌ Ошибка при расчете баланса: {e}")
            return 0

    def has_future_lessons(self, student_id):
        today = self._get_today()
        query = "SELECT COUNT(*) FROM lessons WHERE student_id = ? AND lesson_date > ?"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (student_id, today))
                return cursor.fetchone()[0] > 0
        except:
            return False

    def get_financial_status(self, student_id, balance):
        if balance < 0:
            return "🔴", f"Долг: {abs(balance)} PLN"
        
        has_lessons = self.has_future_lessons(student_id)

        if balance == 0:
            if has_lessons:
                return "🟡", "Пора оплатить (есть запись)"
            else:
                return "⚪️", "Нет активных занятий"

        # Если balance > 0
        if has_lessons:
            return "🟢", f"Оплачено (баланс {balance} PLN)"
        else:
            return "🟢", f"Запас: {balance} PLN (нет записей)"