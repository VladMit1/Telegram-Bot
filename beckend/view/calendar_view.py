import calendar
from datetime import datetime
from telebot import types
from database.db_manager import db # Импортируем базу

def create_calendar(student_id, year=None, month=None , mode="view", highlight_dates=None):
    now = datetime.now()
    curr_year = year or now.year
    curr_month = month or now.month
    # Если список дат не передан, делаем пустым
    if highlight_dates is None:
        highlight_dates = []
		# Получаем дни с занятиями
    busy_days = db.get_busy_days(student_id, curr_year, curr_month)
    markup = types.InlineKeyboardMarkup(row_width=7)
    
    # Заголовок: Месяц и Год
    months_ru = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", 
                 "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    
    header_btn = types.InlineKeyboardButton(f"{months_ru[curr_month]} {curr_year}", callback_data="ignore")
    markup.row(header_btn)

    # Дни недели
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    row = [types.InlineKeyboardButton(d, callback_data="ignore") for d in days]
    markup.row(*row)

    # Сетка чисел
    month_calendar = calendar.monthcalendar(curr_year, curr_month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(" ", callback_data="ignore"))
            else:
               # ФОРМИРУЕМ ТЕКСТ КНОПКИ
                date_str = f"{curr_year}-{curr_month:02d}-{day:02d}"
                prefix = ""
                
                if mode == "pay":
                    # Если в этот день была оплата — ставим монетку
                    if date_str in highlight_dates:
                        prefix = "💰 "
                else:
                    # Если режим обычный — ставим точку занятия
                    if day in busy_days:
                        prefix = "🔹 "
                
                # Пометка сегодняшнего дня (если нет монетки/занятия)
                if day == now.day and curr_month == now.month and curr_year == now.year and not prefix:
                    prefix = "📍 "
                
                btn_text = f"{prefix}{day}"
                
                # CALLBACK меняется в зависимости от режима
                if mode == "pay":
                    callback = f"pay_date_{student_id}_{date_str}"
                else:
                    callback = f"cal_day_{student_id}_{curr_year}_{curr_month}_{day}"
                    
                row.append(types.InlineKeyboardButton(btn_text, callback_data=callback))
        markup.row(*row)

    # Кнопка отмены
    markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data="show_all"))
    
    return markup