import sys
import os
from telebot import types

# Твои импорты путей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from helper.ui_utils import save_last_msg, delete_last_msg
from helper.button_text_align import AlignedMarkup
def get_main_markup():
    """Главное меню (одиночная кнопка)"""
    builder = AlignedMarkup(row_width=1)
    builder.add("➕ Добавить ученика", callback_data="add_student")
    return builder.get_markup()
def render_student_card(bot, chat_id, student_data, finance, is_edit=False, is_search=False, show_add_button=False):
    """Карточка ученика (Адаптированная под словари)"""
    
    # ПРОВЕРКА: Если вдруг пришел список (старый формат), 
    # этот блок позволит коду не упасть, но лучше везде использовать словари
    if isinstance(student_data, (list, tuple)):
        # Если пришел кортеж, превращаем в словарь (на всякий случай)
        s_id = student_data[0]
        name = student_data[1]
        phone = student_data[2]
        date_added = student_data[3]
        photo_id = student_data[4]
        username = student_data[11] if len(student_data) > 11 else "None"
    else:
        # ОСНОВНОЙ ВАРИАНТ (Словарь из нового StudentRepo)
        s_id = student_data['id']
        name = student_data['name']
        phone = student_data['phone']
        date_added = student_data['created_at'] # В базе поле называется created_at
        photo_id = student_data['photo_id']
        username = student_data['username']
    
    actual_balance = finance.get_actual_balance(s_id)
    status_emoji, status_text = finance.get_financial_status(s_id, actual_balance)

    width_fixer = "ㅤ" * 22 
    divider = "──────────────────────────"
    
    # Твоя логика ссылки на чат
    target = None
    if phone and not str(phone).startswith('id_'):
        target = phone
    elif username and str(username) != "None":
        target = username

    chat_url = f"https://t.me/{str(target).replace('@', '').strip()}" if target else None

    # Конструктор кнопок (твоя AlignedMarkup)
    builder = AlignedMarkup(row_width=2)
    if chat_url:
        builder.add("💬 Написать", url=chat_url)
    else:
        builder.add("💬 ———", callback_data="none")
    
    builder.add("📅 График", callback_data=f"open_calendar_{s_id}")
    builder.add("🎥 Урок", callback_data=f"start_lesson_{s_id}")
    builder.add("💳 Пополнить", callback_data=f"pay_{s_id}")
    builder.add("📋 Платежи", callback_data=f"history_pay_{s_id}")
    builder.add("📊 Отчет", web_app=types.WebAppInfo(url=f"https://vladmit1.github.io/Telegram-Bot/?studentId={s_id}"))
    builder.add("⚙️ Опции", callback_data=f"edit_stu_{s_id}")

    markup = builder.get_markup()
    
    if is_search or show_add_button:
        nav_builder = AlignedMarkup(row_width=1)
        if is_search:
            nav_builder.add("🔙 Назад", callback_data="show_all")
        elif show_add_button:
            nav_builder.add("➕ Добавить ученика", callback_data="add_student")
        
        nav_markup = nav_builder.get_markup()
        for row in nav_markup.keyboard:
            markup.keyboard.append(row)

    caption = (f"👤 <b>Ученик:</b> {name}\n"
               f"📱 <b>Тел:</b> <code>{phone if phone and not str(phone).startswith('id_') else 'Не указан'}</code>\n"
               f"📅 <b>Дата:</b> {date_added}\n"
               f"{divider}\n"
               f"{status_emoji} <b>Статус:</b> {status_text}\n"
               f"{width_fixer}")
    
    delete_last_msg(bot, chat_id)

    try:
        if photo_id and str(photo_id) != "None":
            sent_msg = bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="HTML", reply_markup=markup)
        else:
            sent_msg = bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)
        
        save_last_msg(chat_id, sent_msg.message_id)
        return sent_msg.message_id
    except Exception:
        sent_msg = bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)
        save_last_msg(chat_id, sent_msg.message_id)
        return sent_msg.message_id

def render_student_list(bot, chat_id, students, finance):
    """Список учеников (Адаптированный под словари)"""
    markup = types.InlineKeyboardMarkup()
    delete_last_msg(bot, chat_id)

    if not students:
        markup.add(types.InlineKeyboardButton("➕ Добавить первого", callback_data="add_student"))
        sent_msg = bot.send_message(chat_id, "🔎 <b>База учеников пуста</b>", 
                                    parse_mode="HTML", reply_markup=markup)
        save_last_msg(chat_id, sent_msg.message_id)
        return sent_msg.message_id

    student_rows = []
    for i, s in enumerate(students, 1):
        # Используем ключи словаря вместо индексов s[0], s[1]
        s_id = s['id']
        s_name = s['name']
        
        balance = finance.get_actual_balance(s_id)
        status_emoji, _ = finance.get_financial_status(s_id, balance)
        student_rows.append(f"{i}. {status_emoji} /id{s_id} — <b>{s_name}</b> (<code>{balance}</code>)")

    markup.add(types.InlineKeyboardButton("➕ Добавить нового ученика", callback_data="add_student"))
    
    divider = "──────────────────────────"
    msg_text = (
        f"📋 <b>База учеников</b>\n"
        f"{divider}\n"
        f"{'\n'.join(student_rows)}\n"
        f"{divider}\n"
        f"<i>Нажмите на номер /id для просмотра профиля</i>"
    )
    
    sent_msg = bot.send_message(chat_id, msg_text, parse_mode="HTML", reply_markup=markup)
    save_last_msg(chat_id, sent_msg.message_id)
    return sent_msg.message_id