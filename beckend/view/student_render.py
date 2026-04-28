import sys
import os
from telebot import types

# Добавляем корневую папку проекта в пути поиска Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем наш умный сборщик кнопок
from helper.button_text_align import AlignedMarkup

def get_main_markup():
    """Главное меню (одиночная кнопка)"""
    builder = AlignedMarkup(row_width=1)
    builder.add("➕ Добавить ученика", callback_data="add_student")
    return builder.get_markup()

def render_student_card(bot, chat_id, student_data, finance, is_edit=False, message_id=None, is_search=False, show_add_button=False):
    """Карточка ученика с ровными кнопками и прямыми ссылками"""
    student_id = student_data[0]
    name = student_data[1]
    phone = student_data[2]
    date_added = student_data[3]
    photo_id = student_data[4]
    username = student_data[11]
    
    actual_balance = finance.get_actual_balance(student_id)
    status_emoji, status_text = finance.get_financial_status(student_id, actual_balance)

    # Визуальные разделители
    width_fixer = "ㅤ" * 22 
    divider = "──────────────────────────"
    
    # --- ЛОГИКА ССЫЛКИ НА ЧАТ ---
    # 1. Определяем, ЧТО использовать для связи
    # Если телефон настоящий (не id_), он в приоритете
    if phone and not str(phone).startswith('id_'):
        target = phone
    # Если телефон — это id_ или его нет, берем юзернейм
    elif username and str(username) != "None":
        target = username
    else:
        target = None

    # 2. Формируем ссылку, если цель найдена
    chat_url = None
    if target:
        # Убираем собачку (она ломает ссылки t.me/) и лишние пробелы
        clean_val = str(target).replace('@', '').strip()
        chat_url = f"https://t.me/{clean_val}"

    # 3. Твой конструктор кнопок
    builder = AlignedMarkup(row_width=2)
    if chat_url:
        builder.add("💬 Написать", url=chat_url)
    else:
        builder.add("💬 ———", callback_data="none")
    builder.add("📅 График", callback_data=f"open_calendar_{student_id}")
    # ВТОРОЙ РЯД
    builder.add("🎥 Урок", callback_data=f"start_lesson_{student_id}")
    builder.add("💳 Пополнить", callback_data=f"pay_{student_id}")

    # ТРЕТИЙ РЯД
    builder.add("📊 Отчет", web_app=types.WebAppInfo(url=f"https://vladmit1.github.io/Telegram-Bot/?studentId={student_id}"))
    builder.add("⚙️ Опции", callback_data=f"edit_stu_{student_id}")

    # Генерируем основную клавиатуру
    markup = builder.get_markup()
    
    # НИЖНЯЯ НАВИГАЦИЯ (на всю ширину)
    if is_search or show_add_button:
        nav_builder = AlignedMarkup(row_width=1)
        if is_search:
            nav_builder.add("🔙 Назад", callback_data="show_all")
        elif show_add_button:
            nav_builder.add("➕ Добавить ученика", callback_data="add_student")
        
        # Склеиваем ряды
        nav_markup = nav_builder.get_markup()
        for row in nav_markup.keyboard:
            markup.keyboard.append(row)

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

def render_student_list(bot, chat_id, students, finance):
    """Список учеников: кликабельные команды /id в тексте + одна кнопка действия"""
    from telebot import types
    markup = types.InlineKeyboardMarkup()
    
    if not students:
        markup.add(types.InlineKeyboardButton("➕ Добавить первого", callback_data="add_student"))
        return bot.send_message(chat_id, "🔎 <b>База учеников пуста</b>", 
                                parse_mode="HTML", reply_markup=markup).message_id

    student_rows = []
    # Мы больше не создаем список ready_buttons для каждого ученика

    for i, s in enumerate(students, 1):
        s_id, s_name = s[0], s[1]
        balance = finance.get_actual_balance(s_id)
        status_emoji, _ = finance.get_financial_status(s_id, balance)
        
        # Текст строки: 1. ✅ /id123 — Лера (500)
        # Команда /id{s_id} — это и есть наша "невидимая кнопка"
        student_rows.append(f"{i}. {status_emoji} /id{s_id} — <b>{s_name}</b> (<code>{balance}</code>)")

    # Внизу оставляем ТОЛЬКО системные кнопки
    markup.add(types.InlineKeyboardButton("➕ Добавить нового ученика", callback_data="add_student"))
    
    divider = "──────────────────────────"
    msg_text = (
        f"📋 <b>База учеников</b>\n"
        f"{divider}\n"
        f"{'\n'.join(student_rows)}\n"
        f"{divider}\n"
        f"<i>Нажмите на номер /id для просмотра профиля</i>"
    )
    
    return bot.send_message(chat_id, msg_text, parse_mode="HTML", reply_markup=markup).message_id