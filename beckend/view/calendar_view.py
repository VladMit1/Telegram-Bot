import calendar
from datetime import datetime
from telebot import types
from database.db_manager import db

def create_calendar(student_id, year=None, month=None, mode="view", highlight_dates=None):
    now = datetime.now()
    curr_year = year or now.year
    curr_month = month or now.month
    if highlight_dates is None: highlight_dates = []

    # Тот самый невидимый расширитель
    w = "⠀" 
    
    if student_id == "all":
        busy_days = busy_days = db.lessons.get_all_busy_days(curr_year, curr_month)
    else:
        busy_days = db.lessons.get_student_busy_days(student_id, curr_year, curr_month)

    markup = types.InlineKeyboardMarkup(row_width=7)
    
    # 1. ШАПКА (Месяц и Год раздельно для ширины)
    months_ru = ["", "ЯНВАРЬ", "ФЕВРАЛЬ", "МАРТ", "АПРЕЛЬ", "МАЙ", "ИЮНЬ", 
                 "ИЮЛЬ", "АВГУСТ", "СЕНТЯБРЬ", "ОКТЯБРЬ", "НОЯБРЬ", "ДЕКАБРЬ"]
    
    # Год с навигацией
    markup.row(
        types.InlineKeyboardButton("⬅️", callback_data=f"cal_nav_{student_id}_{mode}_{curr_year if curr_month > 1 else curr_year-1}_{curr_month-1 if curr_month > 1 else 12}"),
        types.InlineKeyboardButton(f"{w*4}{curr_year}{w*4}", callback_data="ignore"),
        types.InlineKeyboardButton("➡️", callback_data=f"cal_nav_{student_id}_{mode}_{curr_year if curr_month < 12 else curr_year+1}_{curr_month+1 if curr_month < 12 else 1}")
    )
    # Месяц отдельной строкой (растяжка)
    markup.row(types.InlineKeyboardButton(f"{w*7}{months_ru[curr_month]}{w*7}", callback_data="ignore"))

    # 2. ДНИ НЕДЕЛИ
    days = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]
    markup.row(*[types.InlineKeyboardButton(f"{d}", callback_data="ignore") for d in days])

    # 3. СЕТКА ЧИСЕЛ
    month_calendar = calendar.monthcalendar(curr_year, curr_month)
    for week in month_calendar:
        row = []
        for day in week:
            if day == 0:
                row.append(types.InlineKeyboardButton(f"{w}", callback_data="ignore"))
            else:
                date_str = f"{curr_year}-{curr_month:02d}-{day:02d}"
                
                # Формируем текст кнопки
                if day == now.day and curr_month == now.month and curr_year == now.year:
                    # Сегодня — выделяем точками по бокам
                    btn_text = f"•{day}•" 
                elif mode == "pay" and date_str in highlight_dates:
                    # Оплата — монета рядом (вынужденная мера)
                    btn_text = f"{day}💰"
                elif mode != "pay" and day in busy_days:
                    # Урок — синий маркер
                    btn_text = f"{day}🔹"
                else:
                    # Обычный день — добавляем невидимый символ для одинаковой ширины
                    btn_text = f"{w}{day}{w}"

                # Callback
                if student_id == "all": cb = f"all_cal_day_{curr_year}_{curr_month}_{day}"
                elif mode == "pay": cb = f"pay_date_{student_id}_{date_str}"
                else: cb = f"cal_day_{student_id}_{curr_year}_{curr_month}_{day}"
                    
                row.append(types.InlineKeyboardButton(btn_text, callback_data=cb))
        markup.row(*row)

    # 4. ФУТЕР-МАЯК (Раз перенос не работает, сделаем легенду внизу)
    legend = "🔹 - уроки  |  💰 - оплаты  |  • - сегодня"
    markup.row(types.InlineKeyboardButton(legend, callback_data="ignore"))
    markup.row(types.InlineKeyboardButton("🔙 Назад к профилю", callback_data=f"view_stu_{student_id}"))
    
    return markup