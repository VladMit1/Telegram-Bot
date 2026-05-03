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

def render_student_card(bot, chat_id, student_data, finance, is_edit=False, is_search=False, show_add_button=False, edit_msg_id=None):
    """Карточка ученика (Полностью текстовый режим для плавности)"""
    
    # 1. Извлечение данных
    if isinstance(student_data, (list, tuple)):
        s_id, name, phone, date_added = student_data[0], student_data[1], student_data[2], student_data[3]
        username = student_data[11] if len(student_data) > 11 else "None"
    else:
        s_id = student_data['id']
        name = student_data['name']
        phone = student_data['phone']
        date_added = student_data['created_at']
        username = student_data['username']
    
    actual_balance = finance.get_actual_balance(s_id)
    status_emoji, status_text = finance.get_financial_status(s_id, actual_balance)

    width_fixer = "ㅤ" * 22 
    divider = "──────────────────────────"
    
    # 2. Логика кнопок
    target = phone if phone and not str(phone).startswith('id_') else (username if username != "None" else None)
    chat_url = f"https://t.me/{str(target).replace('@', '').strip()}" if target else None

    builder = AlignedMarkup(row_width=2)
    builder.add("💬 Написать", url=chat_url) if chat_url else builder.add("💬 ———", callback_data="none")
    
    builder.add("📅 График", callback_data=f"open_calendar_{s_id}")
    builder.add("🎥 Урок", callback_data=f"start_lesson_{s_id}")
    builder.add("💳 Пополнить", callback_data=f"pay_{s_id}")
    builder.add("📋 Платежи", callback_data=f"history_pay_{s_id}")
    builder.add("📊 Отчет", web_app=types.WebAppInfo(url=f"https://vladmit1.github.io/Telegram-Bot/?studentId={s_id}"))
    builder.add("⚙️ Опции", callback_data=f"edit_stu_{s_id}")

    markup = builder.get_markup()
    
    if is_search or show_add_button:
        nav_builder = AlignedMarkup(row_width=1)
        nav_builder.add("🔙 Назад", callback_data="show_all") if is_search else nav_builder.add("➕ Добавить ученика", callback_data="add_student")
        for row in nav_builder.get_markup().keyboard:
            markup.keyboard.append(row)

    caption = (f"👤 <b>Ученик:</b> {name}\n"
               f"📱 <b>Тел:</b> <code>{phone if phone and not str(phone).startswith('id_') else 'Не указан'}</code>\n"
               f"📅 <b>Дата:</b> {date_added}\n"
               f"{divider}\n"
               f"{status_emoji} <b>Статус:</b> {status_text}\n"
               f"{width_fixer}")

    # 3. ОТПРАВКА ИЛИ РЕДАКТИРОВАНИЕ
    if edit_msg_id:
        try:
            bot.edit_message_text(caption, chat_id, edit_msg_id, reply_markup=markup, parse_mode="HTML")
            return edit_msg_id  # Выходим сразу после редактирования!
        except Exception as e:
            print(f"Ошибка редактирования карточки: {e}")
            # Если не смогли отредактировать, идем ниже и шлем новое

    # Если мы дошли сюда, значит либо edit_msg_id=None, либо редактирование упало
    try:
        # ПЕРЕД отправкой нового удаляем старое, чтобы не копилось
        delete_last_msg(bot, chat_id)
        
        sent_msg = bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)
        save_last_msg(chat_id, sent_msg.message_id)
        return sent_msg.message_id
    except Exception as e:
        print(f"Ошибка отправки карточки: {e}")
        return None

def render_student_list(bot, chat_id, students, finance, edit_msg_id=None):
    """Список учеников: либо редактирует, либо шлет новое. Без дублей."""
    markup = types.InlineKeyboardMarkup()
    
    # Сборка текста (тут всё без изменений)
    if not students:
        markup.add(types.InlineKeyboardButton("➕ Добавить первого", callback_data="add_student"))
        msg_text = "🔎 <b>База учеников пуста</b>"
    else:
        student_rows = []
        for i, s in enumerate(students, 1):
            s_id, s_name = s['id'], s['name']
            balance = finance.get_actual_balance(s_id)
            status_emoji, _ = finance.get_financial_status(s_id, balance)
            student_rows.append(f"{i}. {status_emoji} /id{s_id} — <b>{s_name}</b> (<code>{balance}</code>)")

        markup.add(types.InlineKeyboardButton("➕ Добавить нового ученика", callback_data="add_student"))
        msg_text = (f"📋 <b>База учеников</b>\n──────────────────────────\n"
                    f"{'\n'.join(student_rows)}\n──────────────────────────\n"
                    f"<i>Нажмите на номер /id для просмотра профиля</i>")

    # ВАЖНЫЙ БЛОК:
    if edit_msg_id:
        try:
            bot.edit_message_text(msg_text, chat_id, edit_msg_id, reply_markup=markup, parse_mode="HTML")
            return edit_msg_id  # <--- КРИТИЧНО: выходим из функции здесь!
        except Exception as e:
            print(f"Edit failed: {e}") 
            # Если не смогли отредактировать (например, текст совпадает), 
            # просто выходим, чтобы не плодить сообщения
            return edit_msg_id

    # Сюда код дойдет ТОЛЬКО если edit_msg_id равен None
    delete_last_msg(bot, chat_id)
    sent_msg = bot.send_message(chat_id, msg_text, parse_mode="HTML", reply_markup=markup)
    save_last_msg(chat_id, sent_msg.message_id)
    return sent_msg.message_id