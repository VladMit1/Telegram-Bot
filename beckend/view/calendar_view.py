import calendar
from datetime import datetime
from telebot import types

# Словарь для маленьких цифр
SMALL_NUMS = {
    '0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', 
    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'
}

def to_small(n):
    """Конвертирует число в маленькие подстрочные цифры"""
    return "".join(SMALL_NUMS.get(char, char) for str_n in [str(n)] for char in str_n)

def create_calendar(student_id, year=None, month=None, mode="view", highlight_dates=None, db=None):
    now = datetime.now()
    curr_year = int(year) if year else now.year
    curr_month = int(month) if month else now.month
    if highlight_dates is None: highlight_dates = []

    # Тот самый невидимый символ-распорка (U+2800)
    w = "⠀" 
    
    # 1. ЗАГРУЗКА ДАННЫХ ИЗ БД
    if db:
        if str(student_id) == "all":
            busy_days = db.lessons.get_all_busy_days(curr_year, curr_month)
        else:
            busy_days = db.lessons.get_student_busy_days(student_id, curr_year, curr_month)
    else:
        busy_days = [] # Заглушка, если БД не передана

    markup = types.InlineKeyboardMarkup(row_width=7)
    
    # 2. ШАПКА: НАВИГАЦИЯ
    prev_m, prev_y = (curr_month-1, curr_year) if curr_month > 1 else (12, curr_year-1)
    next_m, next_y = (curr_month+1, curr_year) if curr_month < 12 else (1, curr_year+1)
    
    months_ru = ["", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", 
                "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]

    # Ряд 1: Год (кликабельный) и стрелки по бокам
    markup.row(
        types.InlineKeyboardButton("⏪ Назад", callback_data=f"cal_nav_{student_id}_{mode}_{prev_y}_{prev_m}"),
        types.InlineKeyboardButton(f"{curr_year}", callback_data=f"open_years_{student_id}_{mode}_{curr_year}"),
        types.InlineKeyboardButton("Вперед ⏩", callback_data=f"cal_nav_{student_id}_{mode}_{next_y}_{next_m}")
    )
    
    # Ряд 2: Месяц (кликабельный) на всю ширину
    markup.row(
        types.InlineKeyboardButton(f"📅 {months_ru[curr_month]}", callback_data=f"open_months_{student_id}_{mode}_{curr_year}")
    )
    
    # Ряд 3: Дни недели
    days_header = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    markup.row(*[types.InlineKeyboardButton(d, callback_data="ignore") for d in days_header])

    # 3. СЕТКА ЧИСЕЛ
    month_calendar = calendar.monthcalendar(curr_year, curr_month)
    
    for week in month_calendar:
        row_buttons = []
        for day in week:
            if day == 0:
                # Пустая кнопка с распоркой
                row_buttons.append(types.InlineKeyboardButton(w, callback_data="ignore"))
                continue
            
            date_str = f"{curr_year}-{curr_month:02d}-{day:02d}"
            is_today = (day == now.day and curr_month == now.month and curr_year == now.year)
            has_lesson = (day in busy_days)
            has_pay = (date_str in highlight_dates)
            
            s_day = to_small(day)

            # Логика иконок
            if is_today and has_lesson: 
                btn_text = f"🧧{s_day}"
            elif is_today: 
                btn_text = f"📍{day}" # Сегодня без урока оставляем крупным
            elif has_lesson and has_pay: 
                btn_text = f"❇️{s_day}"
            elif has_lesson: 
                btn_text = f"🔹{s_day}"
            elif has_pay: 
                btn_text = f"🔸{s_day}"
            else: 
                btn_text = str(day)

            # Callback
            if str(student_id) == "all":
                cb = f"all_cal_day_{curr_year}_{curr_month}_{day}"
            elif mode == "pay":
                cb = f"pay_date_{student_id}_{date_str}"
            else:
                cb = f"cal_day_{student_id}_{curr_year}_{curr_month}_{day}"
                
            row_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=cb))
        markup.row(*row_buttons)

    # ДОБИВКА ДО 6 РЯДОВ (чтобы кнопки не прыгали)
    for _ in range(6 - len(month_calendar)):
        markup.row(*[types.InlineKeyboardButton(w, callback_data="ignore") for _ in range(7)])

    # 4. ПОДВАЛ И ЛЕГЕНДА
    legend = "🧧-сегодня урок |🔹-урок |🔸-оплата |❇️-урок и оплата"
    markup.row(types.InlineKeyboardButton(legend, callback_data="ignore"))

    if str(student_id) == "all":
        markup.row(types.InlineKeyboardButton("🔙 К списку учеников", callback_data='show_all'))
    else:
        markup.row(types.InlineKeyboardButton("👤 В профиль ученика", callback_data=f"fast_view_{student_id}"))
    
    return markup

# --- ВСПОМОГАТЕЛЬНЫЕ СЕТКИ ВЫБОРА ---

def create_months_select(student_id, mode, year):
    markup = types.InlineKeyboardMarkup(row_width=3)
    months_ru = ["", "Янв", "Фев", "Мар", "Апр", "Май", "Июн", 
                "Июл", "Авг", "Сен", "Окт", "Ноя", "Дек"]
    
    btns = []
    for m in range(1, 13):
        btns.append(types.InlineKeyboardButton(
            months_ru[m], 
            callback_data=f"cal_nav_{student_id}_{mode}_{year}_{m}"
        ))
    markup.add(*btns)
    
    # Отмена ведет на текущий месяц этого года
    markup.add(types.InlineKeyboardButton("🔙 Отмена", callback_data=f"cal_nav_{student_id}_{mode}_{year}_{datetime.now().month}"))
    return markup

def create_years_select(student_id, mode, current_year):
    markup = types.InlineKeyboardMarkup(row_width=3)
    y_int = int(current_year)
    
    btns = []
    for y in range(y_int - 4, y_int + 5):
        btns.append(types.InlineKeyboardButton(
            f"• {y} •" if y == y_int else str(y), 
            callback_data=f"cal_nav_{student_id}_{mode}_{y}_1"
        ))
    markup.add(*btns)
    
    # Отмена ведет на январь текущего года
    markup.add(types.InlineKeyboardButton("🔙 Отмена", callback_data=f"cal_nav_{student_id}_{mode}_{y_int}_1"))
    return markup # УБРАЛИ ЗАПЯТУЮ И ЛИШНИЙ ТЕКСТ