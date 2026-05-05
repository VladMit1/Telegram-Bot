import calendar
from datetime import datetime
from telebot import types
from database.db_manager import db

def create_calendar(student_id, year=None, month=None, mode="view", highlight_dates=None):
    now = datetime.now()
    curr_year = int(year) if year else now.year
    curr_month = int(month) if month else now.month
    if highlight_dates is None: highlight_dates = []

    w = "⠀" # Невидимый символ
    
    # 1. ЗАГРУЗКА ДАННЫХ
    if str(student_id) == "all":
        busy_days = db.lessons.get_all_busy_days(curr_year, curr_month)
    else:
        busy_days = db.lessons.get_student_busy_days(student_id, curr_year, curr_month)

    markup = types.InlineKeyboardMarkup(row_width=7)
    
    # 2. ШАПКА: НАВИГАЦИЯ (РАСПЛЫВАЕТСЯ ПО КРАЯМ)
    prev_m, prev_y = (curr_month-1, curr_year) if curr_month > 1 else (12, curr_year-1)
    next_m, next_y = (curr_month+1, curr_year) if curr_month < 12 else (1, curr_year+1)
    
    months_ru = ["", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", 
                "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]
    w = "⠀" # Тот самый невидимый символ
    spacer = w * 15 # Дублируем его 15 раз
    # Ряд 1: Стрелки по бокам и пустая кнопка-распорка между ними
    markup.row(
        types.InlineKeyboardButton("⏪ Назад", callback_data=f"cal_nav_{student_id}_{mode}_{prev_y}_{prev_m}"),
        types.InlineKeyboardButton(spacer, callback_data="ignore"),
        types.InlineKeyboardButton("Вперед ⏩", callback_data=f"cal_nav_{student_id}_{mode}_{next_y}_{next_m}")
    )
    
    # Ряд 2: Месяц и Год на всю ширину (отдельной строкой)
    markup.row(
        types.InlineKeyboardButton(f"📅 {months_ru[curr_month]} {curr_year}", callback_data="ignore")
    )
    
    days_header = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in days_header])

    # 3. СЕТКА ЧИСЕЛ (ФИКСАЦИЯ 6 РЯДОВ)
    month_calendar = calendar.monthcalendar(curr_year, curr_month)
    SMALL_NUMS = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', 
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
    }

    def to_small(n):
        return "".join(SMALL_NUMS.get(char, char) for char in str(n))
    # Рисуем основные недели месяца
    for week in month_calendar:
        row_buttons = []
        for day in week:
            if day == 0:
                row_buttons.append(types.InlineKeyboardButton(w, callback_data="ignore"))
                continue
            
            date_str = f"{curr_year}-{curr_month:02d}-{day:02d}"
            is_today = (day == now.day and curr_month == now.month and curr_year == now.year)
            has_lesson = (day in busy_days)
            has_pay = (date_str in highlight_dates)
            s_day = to_small(day)
            if is_today and has_lesson: btn_text = f"🧧{s_day}"
            elif is_today: btn_text = f"📍{day}"
            elif has_lesson and has_pay: btn_text = f"❇️{s_day}"
            elif has_lesson: btn_text = f"🔹{s_day}"
            elif has_pay: btn_text = f"🔸{s_day}"
            else: btn_text = str(day)

            if str(student_id) == "all":
                cb = f"all_cal_day_{curr_year}_{curr_month}_{day}"
            elif mode == "pay":
                cb = f"pay_date_{student_id}_{date_str}"
            else:
                cb = f"cal_day_{student_id}_{curr_year}_{curr_month}_{day}"
                
            row_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=cb))
        markup.row(*row_buttons)

    # --- ВОТ ТУТ МАГИЯ: Добиваем пустые ряды до 6 штук ---
    full_rows = len(month_calendar)
    for _ in range(6 - full_rows):
        empty_row = [types.InlineKeyboardButton(w, callback_data="ignore") for _ in range(7)]
        markup.row(*empty_row)

    # 4. ПОДВАЛ И ЛЕГЕНДА (Теперь всегда)
    legend = "🧧-сегодня урок |🔹-урок |🔸-оплата |❇️-урок и оплата"
    markup.row(types.InlineKeyboardButton(legend, callback_data="ignore"))

    # Кнопки выхода
    if str(student_id) == "all":
        markup.row(types.InlineKeyboardButton("🔙 К списку учеников", callback_data='show_all'))
    else:
        markup.row(types.InlineKeyboardButton("👤 В профиль ученика", callback_data=f"fast_view_{student_id}"))
    
    return markup