import calendar
from datetime import datetime
from telebot import types
from database.db_manager import db

def create_calendar(student_id, year=None, month=None, mode="view", highlight_dates=None):
    """
    Универсальный календарь:
    - student_id: ID ученика или "all" для общего расписания
    - mode: "view" (уроки) или "pay" (оплаты)
    - highlight_dates: список дат с монетами для режима "pay"
    """
    now = datetime.now()
    curr_year = year or now.year
    curr_month = month or now.month
    
    if highlight_dates is None:
        highlight_dates = []

    # 1. ПОЛУЧАЕМ ДАННЫЕ ИЗ БАЗЫ
    if student_id == "all":
        # Метод для получения всех занятых дней месяца всеми учениками
        busy_days = db.get_all_busy_days(curr_year, curr_month)
    else:
        # Метод для получения занятых дней конкретного ученика
        busy_days = db.get_busy_days(student_id, curr_year, curr_month)

    markup = types.InlineKeyboardMarkup(row_width=7)
    
    # 2. НАВИГАЦИЯ (РАСЧЕТ СЛЕДУЮЩЕГО/ПРЕДЫДУЩЕГО МЕСЯЦА)
    prev_month = curr_month - 1 if curr_month > 1 else 12
    prev_year = curr_year if curr_month > 1 else curr_year - 1
    
    next_month = curr_month + 1 if curr_month < 12 else 1
    next_year = curr_year if curr_month < 12 else curr_year + 1

    months_ru = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                 "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    # Ряд управления: [ < ] [ Месяц Год ] [ > ]
    # Передаем student_id и mode, чтобы навигация не сбивала контекст
    row_nav = [
        types.InlineKeyboardButton("⬅️", callback_data=f"cal_nav_{student_id}_{mode}_{prev_year}_{prev_month}"),
        types.InlineKeyboardButton(f"{months_ru[curr_month]} {curr_year}", callback_data="ignore"),
        types.InlineKeyboardButton("➡️", callback_data=f"cal_nav_{student_id}_{mode}_{next_year}_{next_month}")
    ]
    markup.row(*row_nav)

    # 3. ДНИ НЕДЕЛИ
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in days])

    # 4. СЕТКА ЧИСЕЛ
    month_calendar = calendar.monthcalendar(curr_year, curr_month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                date_str = f"{curr_year}-{curr_month:02d}-{day:02d}"
                prefix = ""
                
                # Логика иконок (Префикс)
                if mode == "pay":
                    # Режим оплаты: только монетки
                    if date_str in highlight_dates:
                        prefix = "💰 "
                else:
                    # Режим уроков: синие точки
                    if day in busy_days:
                        prefix = "🔹 "
                
                # Пометка сегодняшнего дня (📍), если нет других иконок
                if day == now.day and curr_month == now.month and curr_year == now.year and not prefix:
                    prefix = "📍 "
                
                btn_text = f"{prefix}{day}"
                
                # ОПРЕДЕЛЯЕМ CALLBACK В ЗАВИСИМОСТИ ОТ ТИПА
                if student_id == "all":
                    # Клик в общем календаре -> список уроков дня
                    callback = f"all_cal_day_{curr_year}_{curr_month}_{day}"
                elif mode == "pay":
                    # Клик в фин. календаре -> ввод суммы
                    callback = f"pay_date_{student_id}_{date_str}"
                else:
                    # Клик в календаре ученика -> выбор времени занятия
                    callback = f"cal_day_{student_id}_{curr_year}_{curr_month}_{day}"
                    
                row.append(types.InlineKeyboardButton(btn_text, callback_data=callback))
        markup.row(*row)
    # --- ДОБАВЛЕНИЕ ПУСТЫХ РЯДОВ ДО 6 ШТУК ---
    # Проверяем, сколько недель (рядов) уже отрисовано
    rows_count = len(month_calendar)
    while rows_count < 6:
        empty_row = [types.InlineKeyboardButton(" ", callback_data="ignore") for _ in range(7)]
        markup.row(*empty_row)
        rows_count += 1
    # ----------------------------------------
    # 5. КНОПКА ОТМЕНЫ / НАЗАД
    markup.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="show_all"))
    
    return markup