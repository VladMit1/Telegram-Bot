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

        if balance > 0:
            if has_future:
                return "🟢", f"Оплачено ({balance} PLN)"
            else:
                return "✅", f"Баланс: {balance} PLN"

    def get_student_history_by_months(self, student_id):
        """Детальная история ученика: Месяц | Оплачено | Отработано"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
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

    # --- МЕТОДЫ ДЛЯ ОБЩИХ ОТЧЕТОВ ПО ГОДАМ ---

    def get_available_years(self):
        """Возвращает уникальные года из БД (из платежей и уроков)"""
        query = """
            SELECT DISTINCT strftime('%Y', payment_date) as year FROM payments WHERE payment_date IS NOT NULL
            UNION
            SELECT DISTINCT strftime('%Y', lesson_date) as year FROM lessons WHERE lesson_date IS NOT NULL
            ORDER BY year ASC
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
        
        years = [int(r[0]) for r in rows if r[0] and str(r[0]).isdigit()]
        current_year = datetime.now().year
        return sorted(list(set(years))) if years else [current_year]

    def get_yearly_report(self, year):
        """Финансовый отчет за конкретный выбранный год"""
        year_str = str(year)
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Зашло денег за год
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM payments 
                WHERE strftime('%Y', payment_date) = ?
            """, (year_str,))
            total_income = cursor.fetchone()[0]

            # 2. Отработано уроков за год
            cursor.execute("""
                SELECT COALESCE(SUM(lesson_price), 0) 
                FROM lessons 
                WHERE strftime('%Y', lesson_date) = ?
            """, (year_str,))
            total_spent = cursor.fetchone()[0]

        return {
            'year': year,
            'total_income': total_income,
            'total_spent': total_spent,
            'net_balance': total_income - total_spent
        }

    def get_total_yearly_stats(self):
        """Общая касса по годам"""
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
        """Общий глобальный отчет за все время"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
        
            # 1. Всего зашло денег
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
            total_income = cursor.fetchone()[0]
        
            # 2. Всего проведено уроков
            cursor.execute("SELECT COALESCE(SUM(lesson_price), 0) FROM lessons")
            total_spent = cursor.fetchone()[0]
        
            # 3. Суммарный долг учеников (работает с вашей таблицей contacts)
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
            'balance_in_system': total_income - total_spent,
            'total_debt': abs(total_debt)
        }

    # =========================================================================
    # ДОБАВЛЕННЫЕ МЕТОДЫ ДЛЯ ФИНОТЧЕТА ПО УЧЕНИКУ
    # =========================================================================

    def get_student_years(self, student_id):
        """Возвращает список уникальных годов активности ученика (с поддержкой разных форматов дат)."""
        sid = int(student_id) if str(student_id).isdigit() else student_id

        query = """
            SELECT DISTINCT 
                CASE 
                    WHEN payment_date LIKE '____-__-__%' THEN substr(payment_date, 1, 4)
                    WHEN payment_date LIKE '__.__.____%' THEN substr(payment_date, 7, 4)
                    ELSE strftime('%Y', payment_date)
                END as year 
            FROM payments WHERE student_id = ? AND payment_date IS NOT NULL

            UNION

            SELECT DISTINCT 
                CASE 
                    WHEN lesson_date LIKE '____-__-__%' THEN substr(lesson_date, 1, 4)
                    WHEN lesson_date LIKE '__.__.____%' THEN substr(lesson_date, 7, 4)
                    ELSE strftime('%Y', lesson_date)
                END as year 
            FROM lessons WHERE student_id = ? AND lesson_date IS NOT NULL
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (sid, sid))
            rows = cursor.fetchall()
        
        years = [int(r[0]) for r in rows if r[0] and str(r[0]).isdigit()]
        current_year = datetime.now().year
        
        if not years:
            years = [current_year]
            
        return sorted(list(set(years)))
    def get_student_yearly_report(self, student_id, year):
        """Показатели ученика за выбранный год: количество уроков, их сумма и оплачено"""
        year_str = str(year)
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Количество и сумма уроков
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(lesson_price), 0) 
                FROM lessons 
                WHERE student_id = ? AND strftime('%Y', lesson_date) = ?
            """, (student_id, year_str))
            row_lessons = cursor.fetchone()
            lessons_count = row_lessons[0] or 0
            spent = row_lessons[1] or 0

            # 2. Сумма оплат
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM payments 
                WHERE student_id = ? AND strftime('%Y', payment_date) = ?
            """, (student_id, year_str))
            paid = cursor.fetchone()[0] or 0

        return {
            'lessons_count': lessons_count,
            'spent': spent,
            'paid': paid
        }

    def get_student_global_report(self, student_id):
        """Итоговые показатели ученика за всё время работы"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Всего уроков и их стоимость
            cursor.execute("""
                SELECT COUNT(*), COALESCE(SUM(lesson_price), 0) 
                FROM lessons 
                WHERE student_id = ?
            """, (student_id,))
            row_lessons = cursor.fetchone()
            total_lessons = row_lessons[0] or 0
            total_spent = row_lessons[1] or 0

            # 2. Всего оплачено
            cursor.execute("""
                SELECT COALESCE(SUM(amount), 0) 
                FROM payments 
                WHERE student_id = ?
            """, (student_id,))
            total_paid = cursor.fetchone()[0] or 0

        return {
            'total_lessons': total_lessons,
            'total_spent': total_spent,
            'total_paid': total_paid,
            'balance': total_paid - total_spent
        }