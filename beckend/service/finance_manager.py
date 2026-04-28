import sqlite3
from datetime import datetime

class FinanceManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_today(self):
        return datetime.now().strftime('%Y-%m-%d')

    def get_actual_balance(self, student_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Явно выбираем нужные колонки. Теперь:
                # contact[0] - это balance
                # contact[1] - это lesson_price
                # contact[2] - это lesson_price_updated_at
                cursor.execute("""
                    SELECT balance, lesson_price, lesson_price_updated_at 
                    FROM contacts 
                    WHERE id = ?
                """, (student_id,))
                
                contact = cursor.fetchone()
                if not contact: 
                    return 0
            
                base_balance = contact[0]
                current_price = contact[1]
                beacon_date = contact[2] if contact[2] else '2024-01-01 00:00:00'

                # 1. Считаем все уроки после "маяка"
                cursor.execute("""
                    SELECT COUNT(*) FROM lessons 
                    WHERE student_id = ? 
                    AND date(lesson_date) >= date(?)
                    AND date(lesson_date) <= date('now')
                """, (student_id, beacon_date))
                lessons_count = cursor.fetchone()[0]

                # 2. Считаем все оплаты после "маяка"
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0) FROM payments 
                    WHERE student_id = ? 
                    AND date(payment_date) >= date(?)
                """, (student_id, beacon_date))
                payments_sum = cursor.fetchone()[0]

                # Итоговый баланс
                # 0 + 0 - (1 * 50) = -50
                actual_balance = base_balance + payments_sum - (lessons_count * current_price)
                return actual_balance

        except Exception as e:
            print(f"Ошибка в расчете баланса: {e}")
            return 0
    def has_future_lessons(self, student_id):
        today = self._get_today()
        # Смени > на >= чтобы бот видел сегодняшний урок как "активное занятие"
        query = "SELECT COUNT(*) FROM lessons WHERE student_id = ? AND date(lesson_date) >= date(?)"
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
        
        has_future = self.has_future_lessons(student_id)

        if balance == 0:
            return ("🟡", "Пора оплатить (есть запись)") if has_future else ("⚪️", "Нет активных занятий")

        # Если balance > 0
        return ("🟢", f"Оплачено ({balance} PLN)") if has_future else ("✅", f"Баланс: {balance} PLN")