from database.base import BaseDB
from typing import Any, cast
class LessonRepo(BaseDB):
    def add(self, student_id, date, time, student_repo):
        try:
            # Получаем актуальную цену из таблицы contacts
            student = student_repo.get_by_id(student_id)
            price = student['lesson_price'] # Вот она, твоя 50 (или сколько там у ученика)

            # Записываем В ТАБЛИЦУ УРОКОВ
            query = """
                INSERT INTO lessons (student_id, lesson_date, lesson_time, lesson_price) 
                VALUES (?, ?, ?, ?)
            """
            # Если ты тут забыл передать price, то в таблицу уроков запишется 0 
            # (потому что при ALTER TABLE ты скорее всего указал DEFAULT 0)
            self.execute(query, (student_id, date, time, price))
            return True
        except Exception as e:
            print(f"Ошибка при сохранении урока: {e}")
            return False

    def delete(self, date, time, s_id, student_repo, is_refund=False):
        """
        Удаляет урок. 
        is_refund=True — вернуть деньги на баланс.
        is_refund=False — просто удалить запись (по умолчанию).
        """
        
        # 1. Проверяем наличие ученика
        student = student_repo.get_by_id(s_id)
        if not student:
            return False, "Ученик не найден"

        # 2. Удаляем урок
        deleted_count = self.execute(
            "DELETE FROM lessons WHERE lesson_date = ? AND lesson_time = ? AND student_id = ?",
            (date, time, s_id), commit=True
        )

        if deleted_count > 0:
            # 3. Возвращаем деньги ТОЛЬКО если is_refund=True
            if is_refund:
                lesson_price = student['lesson_price']
                return True, f"Урок удален, {lesson_price} PLN возвращено."
            
            return True, "Урок удален без возврата средств."
        
        return False, "Урок не найден в базе данных."

    def get_booked_by_date(self, date):
        query = """
            SELECT l.lesson_time, l.student_id, c.name 
            FROM lessons l JOIN contacts c ON l.student_id = c.id 
            WHERE l.lesson_date = ?
        """
        rows = self.execute(query, (date,), fetchall=True)
        
        # Если rows не список, возвращаем пустой словарь
        if not isinstance(rows, list):
            return {}

        # Безопасная сборка словаря по именам колонок
        return {
            r['lesson_time']: {'id': r['student_id'], 'name': r['name']} 
            for r in rows
        }

    def get_student_busy_days(self, s_id, year, month):
        month_str = f"{year}-{str(month).zfill(2)}%"
        rows = self.execute(
            "SELECT DISTINCT lesson_date FROM lessons WHERE student_id = ? AND lesson_date LIKE ?",
            (s_id, month_str), 
            fetchall=True
        )
        
        # Проверка: если execute вернул число (int), значит данных нет или ошибка
        if not isinstance(rows, list):
            return []

        # Извлекаем день из даты 'YYYY-MM-DD'
        # Обращаемся к row['lesson_date'], это надежнее чем row[0]
        try:
            return [int(str(r['lesson_date']).split('-')[2]) for r in rows]
        except (IndexError, TypeError, KeyError):
            return []
    
    # Файл: database/repos/lesson_repo.py
    def get_lesson_id(self, date, time, student_id):
        row = self.execute(
            "SELECT id FROM lessons WHERE lesson_date = ? AND lesson_time = ?", 
            (date, time), 
            fetchone=True
        )
        # Теперь анализатор знает, что row - это словарь, и разрешает ['id']
        if row:
            return row['id'] 
        return None
    # database/repos/lesson_repo.py

    def auto_lesson_check_in(self, student_id, student_repo):
        from datetime import datetime, timedelta
        now = datetime.now()
    
        # Твоя логика округления (оставляем как есть)
        if now.minute > 30:
            rounded_time = now + timedelta(hours=1)
            time_str = rounded_time.strftime("%H:00")
        else:
            time_str = now.strftime("%H:00")

        date_str = now.strftime("%Y-%m-%d")

        try:
            # УБИРАЕМ student_id из условия! 
            # Проверяем занятость времени ЛЮБЫМ учеником
            query = """
                SELECT c.name FROM lessons l 
                JOIN contacts c ON l.student_id = c.id 
                WHERE l.lesson_date = ? AND l.lesson_time = ?
            """
            existing = self.execute(query, (date_str, time_str), fetchone=True)

            if existing:
                # Теперь мы знаем даже ИМЯ того, кто занял время
                return False, f"{existing['name']}" # Возвращаем имя для алерта

            # Если никто не найден — записываем
            success = self.add(student_id, date_str, time_str, student_repo)
            return (True, time_str) if success else (False, "Ошибка сохранения")

        except Exception as e:
            return False, f"Ошибка: {e}"
    def get_all_busy_days(self, year, month):
        query = """
            SELECT DISTINCT strftime('%d', lesson_date) as day
            FROM lessons 
            WHERE strftime('%Y', lesson_date) = ? 
            AND strftime('%m', lesson_date) = ?
        """
        try:
            res = self.execute(query, (str(year), f"{month:02d}"), fetchall=True)
            # Теперь обращаемся по ключу 'day'
            return [int(row['day']) for row in res] if res else []
        except Exception as e:
            print(f"Error in get_all_busy_days: {e}")
            return []