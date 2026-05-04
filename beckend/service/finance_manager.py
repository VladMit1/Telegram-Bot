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
        
    def get_student_history_by_months(self, student_id):
        """Детальная история ученика: Месяц | Оплачено | Отработано"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Этот запрос объединяет оплаты и уроки, группируя их по месяцам
            query = """
                SELECT 
                    strftime('%m.%Y', date_val) as month_year,
                    SUM(p_amount) as total_paid,
                    SUM(l_price) as total_spent
                FROM (
                    SELECT payment_date as date_val, amount as p_amount, 0 as l_price 
                    FROM payments WHERE student_id = ?
                    UNION ALL
                    SELECT lesson_date as date_val, 0 as p_amount, lesson_price as l_price 
                    FROM lessons WHERE student_id = ?
                )
                GROUP BY month_year
                ORDER BY date_val DESC
                LIMIT 12
            """
            cursor.execute(query, (student_id, student_id))
            return cursor.fetchall()

    def get_total_yearly_stats(self):
        """Общая касса по годам (для главного меню)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT strftime('%Y', payment_date) as year, SUM(amount)
                FROM payments
                GROUP BY year
                ORDER BY year DESC
            """)
            return cursor.fetchall()  

    def get_global_report(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
        
            # 1. Сколько всего реально зашло денег (Все пополнения)
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
            total_income = cursor.fetchone()[0]
        
            # 2. Сколько уроков уже проведено в деньгах
            cursor.execute("SELECT COALESCE(SUM(lesson_price), 0) FROM lessons")
            total_spent = cursor.fetchone()[0]
        
            # 3. Текущая дебиторка (суммарный долг учеников)
            # Считаем разницу для каждого и суммируем только тех, у кого минус
            cursor.execute("""
                SELECT SUM(diff) FROM (
                    SELECT (COALESCE(p.s_paid, 0) - COALESCE(l.s_spent, 0)) as diff
                    FROM contacts c
                    LEFT JOIN (SELECT student_id, SUM(amount) as s_paid FROM payments GROUP BY student_id) p ON c.id = p.student_id
                    LEFT JOIN (SELECT student_id, SUM(lesson_price) as s_spent FROM lessons GROUP BY student_id) l ON c.id = l.student_id
                ) WHERE diff < 0
            """)
        total_debt = cursor.fetchone()[0] or 0

        return {
                'total_income': total_income,
                'total_spent': total_spent,
                'balance_in_system': total_income - total_spent, # Твой "аванс" от учеников
                'total_debt': abs(total_debt)
            }