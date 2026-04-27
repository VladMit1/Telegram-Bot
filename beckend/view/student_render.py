from telebot import types

def get_main_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data="add_student"))
    return markup
def render_student_card(bot, chat_id, student_data, finance,is_edit=False, message_id=None, is_search=False, show_add_button=False):
    student_id = student_data[0]
    name = student_data[1]
    phone = student_data[2]
    date_added = student_data[3]
    photo_id = student_data[4]
    # По твоей таблице: balance - 8, username - 10
    balance = student_data[8]
    username = student_data[10]
    
    # Считаем статус через твой класс finance
    status_emoji, status_text = finance.get_financial_status(student_id, balance)
    
    # 1. ФИКСАТОР ШИРИНЫ (растягивает карточку)
    width_fixer = "ㅤ" * 22  # Невидимые символы
    divider = "──────────────────────────"
    
    # Логика ссылки
    chat_url = None
    if username and username != "None":
        chat_url = f"https://t.me/{str(username).replace('@', '')}"
    elif phone and not str(phone).startswith("id_"):
        clean_phone = "".join(filter(str.isdigit, str(phone)))
        chat_url = f"https://t.me/+{clean_phone}"

    meet_url = f"https://meet.google.com/lookup/lesson-{student_id}"
        
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Ряды кнопок (всегда одинаковое количество для симметрии)
    btn_chat = types.InlineKeyboardButton("💬 Написать", url=chat_url) if chat_url else types.InlineKeyboardButton("💬 ———", callback_data="none")
    markup.add(btn_chat, types.InlineKeyboardButton("📅 Расписание", callback_data=f"open_calendar_{student_id}"))

    markup.add(
        types.InlineKeyboardButton("🎥 Урок", callback_data=f"start_lesson_{student_id}"),
        types.InlineKeyboardButton("💳 Пополнить", callback_data=f"pay_{student_id}")
    )

    markup.add(
        types.InlineKeyboardButton("📊 Статистика", web_app=types.WebAppInfo(url=f"https://vladmit1.github.io/Telegram-Bot/?studentId={student_id}")),
        types.InlineKeyboardButton("⚙️ Настройки", callback_data=f"edit_stu_{student_id}")
    )
    
    if is_search:
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="show_all"))
    elif show_add_button:
        markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data="add_student"))

    caption = (f"👤 <b>Ученик:</b> {name}\n"
               f"📱 <b>Тел:</b> <code>{phone if phone and not str(phone).startswith('id_') else 'Не указан'}</code>\n"
               f"📅 <b>Дата:</b> {date_added}\n"
               f"{divider}\n"
               f"{status_emoji} <b>Статус:</b> {status_text}\n"
               f"{width_fixer}")
    
    try:
        if photo_id:
            return bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="HTML", reply_markup=markup).message_id
        else:
            return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup).message_id
    except Exception as e:
        print(f"Ошибка рендера: {e}")
        return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup).message_id