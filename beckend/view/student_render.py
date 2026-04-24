from telebot import types

def get_main_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data="add_student"))
    return markup

def render_student_card(bot, chat_id, student_data, finance, is_search=False, show_add_button=False):
    # Распаковка индексов
    student_id = student_data[0]
    name = student_data[1]
    phone = student_data[2]
    date_added = student_data[3]
    photo_id = student_data[4]
    username = student_data[10] if len(student_data) > 10 else None
    
    # Считаем живой баланс
    balance = finance.get_actual_balance(student_id)
    status_emoji, status_text = finance.get_financial_status(student_id, balance)
    
    # Логика Telegram-ссылки
    chat_url = None
    if username and username != "None":
        chat_url = f"https://t.me/{str(username).replace('@', '')}"
    elif phone and not str(phone).startswith("id_"):
        clean_phone = "".join(filter(str.isdigit, str(phone)))
        chat_url = f"https://t.me/+{clean_phone}"

    # Логика Google Meet
    meet_url = f"https://meet.google.com/lookup/lesson-{student_id}"
        
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    # Первая строка: Написать (если есть)
    if chat_url:
        markup.add(types.InlineKeyboardButton("💬 Написать", url=chat_url))
    
    # Основные кнопки
    markup.add(
        types.InlineKeyboardButton("🎥 Начать занятие", url=meet_url),
        types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_{student_id}"),
        types.InlineKeyboardButton("📊 Статистика", web_app=types.WebAppInfo(url=f"https://vladmit1.github.io/Telegram-Bot/?studentId={student_id}")),
        types.InlineKeyboardButton("📅 Назначить занятие", callback_data=f"open_calendar_{student_id}")
    )
    
    # Дополнительные кнопки навигации
    if is_search:
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="show_all"))
    
    if show_add_button:
        markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data="add_student"))

    caption = (f"👤 <b>Ученик:</b> {name}\n"
               f"📱 <b>Телефон:</b> <code>{phone if phone and not str(phone).startswith('id_') else 'Не указан'}</code>\n"
               f"📅 <b>Добавлен:</b> {date_added}\n"
               f"──────────────────\n"
               f"{status_emoji} <b>Статус:</b> {status_text}")
    
    try:
        if photo_id:
            return bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="HTML", reply_markup=markup).message_id
        return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup).message_id
    except:
        # Резервный вариант, если фото не загрузилось
        return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup).message_id
