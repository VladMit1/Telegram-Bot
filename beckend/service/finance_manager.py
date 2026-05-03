import sqlite3
from datetime import datetime

class FinanceManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_connection(self):
        """Вспомогательный метод для открытия соединения"""
        return sqlite3.connect(self.db_path)

    def _get_today(self):
        return datetime.now().strftime('%Y-%m-%d')

    def get_actual_balance(self, student_id):
        try:
            with self._get_connection() as conn:
                # Включаем доступ по именам колонок
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 1. Считаем общую сумму всех платежей студента
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) as total_paid 
                    FROM payments 
                    WHERE student_id = ?
                """, (student_id,))
                total_paid = cursor.fetchone()['total_paid']

                # 2. Считаем общую стоимость всех проведенных уроков
                cursor.execute("""
                    SELECT COALESCE(SUM(lesson_price), 0) as total_spent 
                    FROM lessons 
                    WHERE student_id = ?
                """, (student_id,))
                total_spent = cursor.fetchone()['total_spent']

                # Итоговый баланс: Приход - Расход
                return total_paid - total_spent

        except Exception as e:
            print(f"❌ Ошибка в расчете баланса: {e}")
            return 0

    def has_future_lessons(self, student_id):
        today = self._get_today()
        # Сменил > на >= чтобы бот видел сегодняшний урок как "активное занятие"
        query = "SELECT COUNT(*) FROM lessons WHERE student_id = ? AND date(lesson_date) >= date(?)"
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (student_id, today))
                count = cursor.fetchone()[0]
                return count > 0
        except Exception as e:
            print(f"❌ Ошибка в has_future_lessons: {e}")
            return False

    def get_financial_status(self, student_id, balance):
        if balance < 0:
            return "🔴", f"Долг: {abs(balance)} PLN"
        
        has_future = self.has_future_lessons(student_id)

        if balance == 0:
            return ("🟡", "Пора оплатить (есть запись)") if has_future else ("⚪️", "Нет активных занятий")

        # Если balance > 0
        if has_future:
            return "🟢", f"Оплачено ({balance} PLN)"
        else:
            return "✅", f"Баланс: {balance} PLN"