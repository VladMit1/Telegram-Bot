from .base import BaseDB
from .configurator import DBConfigurator
from .repos.student_repo import StudentRepo
from .repos.lesson_repo import LessonRepo
from .repos.payment_repo import PaymentRepo

class DBManager(BaseDB):
    def __init__(self):
        super().__init__()
        # 1. Сначала настраиваем структуру
        DBConfigurator.setup(self.db_path)
        
        # 2. Подключаем репозитории
        self.students = StudentRepo()
        self.lessons = LessonRepo()
        self.payments = PaymentRepo()

    # --- ВЫСОКОУРОВНЕВАЯ ЛОГИКА (Бизнес-логика) ---

    def set_new_lesson_price(self, s_id, new_price, current_balance):
        """Смена цены с фиксацией даты (используем метод репозитория)"""
        from datetime import datetime
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.students.set_price(s_id, new_price, current_balance, today)

# Единственный экземпляр на всё приложение
db = DBManager()