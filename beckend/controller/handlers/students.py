import time
from telebot import types
from view.student_render import render_student_card
import threading
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from view.calendar_view import create_calendar
from datetime import datetime
from helper.error_handler import safe_handler


def register_student_handlers(bot, db, user_data, ui_refs, finance):
    @bot.message_handler(content_types=['contact'])
    @safe_handler(bot)
    def handle_contact(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        contact = message.contact
        
        # Вытягиваем данные
        phone = contact.phone_number
        name = f"{contact.first_name} {contact.last_name or ''}".strip()
        username = message.from_user.username or "None"

        # Сохраняем в базу (используем твой метод)
        db.students.add_contact(name, phone, None, chat_id, f"@{username}")
        
        # Чистый и быстрый способ оповещения:
        msg = bot.send_message(chat_id, f"💎 <b>{name}</b> в базе", parse_mode="HTML")
    
        # Удаляем подтверждение через 2.5 секунды в фоновом потоке
        import threading
        threading.Timer(2.5, lambda: bot.delete_message(chat_id, msg.message_id)).start()
    
        # Сразу возвращаем меню
        ui_refs['handle_start'](message)
    # --- 1. ПЕРЕХОД ПО /id123 (Новое сообщение) ---
    @bot.message_handler(regexp=r"^/id\d+")
    @safe_handler(bot)
    def handle_id_click(message):
        chat_id = message.chat.id
        try:
            # Чистим сообщение пользователя сразу, чтобы не висело
            bot.delete_message(chat_id, message.message_id)
            student_id = int(message.text.replace("/id", ""))
        except: return

        # 1. Показываем лоадинг
        l_id = ui_refs['show_loading'](chat_id, "⌛ <b>Загрузка профиля...</b>")
        
        # 2. Получаем данные
        student_data = db.students.get_by_id(student_id)
        
        if student_data:
            # 3. Чистим экран, КРОМЕ нашего лоадинга
            ui_refs['clear_screen'](chat_id, keep_msg_id=l_id)
            
            # 4. Рендерим карточку СТРОГО через редактирование лоадинга
            # Убедись, что в render_student_card в конце стоит return!
            render_student_card(
                bot, 
                chat_id, 
                student_data, 
                finance, 
                is_search=True, 
                edit_msg_id=l_id  # <--- Подменяем текст лоадинга на карточку
            )
            
            # Обновляем "главное" сообщение бота
            ui_refs['welcome_msg_id'] = l_id 
        else:
            bot.edit_message_text("❌ Ученик не найден", chat_id, l_id)
    # --- 2. БЫСТРЫЙ ПРОФИЛЬ / НАЗАД В ПРОФИЛЬ (Бесшовно) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("fast_view_") or call.data.startswith("view_stu_"))
    @safe_handler(bot) # <-- ТЕПЕРЬ ВСЁ ПОД КОНТРОЛЕМ ЭТОЙ СТРОЧКИ
    def fast_open_card(call):
        chat_id = call.message.chat.id
    
        # Разбираем данные
        parts = call.data.split("_")
        raw_id = parts[2]

        # ПРОВЕРКА: Если это "all", значит это навигация общего календаря,
        # и этот хендлер не должен его обрабатывать.
        if raw_id == "all":
            return 

        student_id = int(raw_id)
        
        # Визуальный отклик
        ui_refs['show_loading'](chat_id, "⌛ <b>Загрузка...</b>", call=call)
        
        student_data = db.students.get_by_id(student_id)
        if student_data:
            # Редактируем текущее сообщение (календарь/настройки) обратно в карточку
            render_student_card(bot, chat_id, student_data, finance, is_search=True, edit_msg_id=call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Ученик не найден", show_alert=True)

    # --- 3. НАСТРОЙКИ (Бесшовно) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_stu_"))
    @safe_handler(bot)
    def student_settings(call):
        chat_id = call.message.chat.id
        student_id = call.data.split("_")[2]
        
        ui_refs['show_loading'](chat_id, "⚙️ <b>Загрузка...</b>", call=call)
        
        student = db.students.get_by_id(student_id)
        if not student: return

        settings_text = (
            f"⚙️ <b>Настройки:</b> {student['name']}\n"
            f"──────────────────────────\n"
            f"💰 <b>Цена:</b> <code>{student['lesson_price']} PLN</code>\n"
            f"📱 <b>Тел:</b> <code>{student['phone'] if not str(student['phone']).startswith('id_') else '—'}</code>"
        )
        
        # Определяем статус для кнопки
        is_active = student.get('status') == 'active'
        archive_btn_text = "📁 В архив" if is_active else "✅ Восстановить"
        archive_callback = f"archive_stu_{student_id}" if is_active else f"restore_stu_{student_id}"

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🏷️ Имя", callback_data=f"edit_name_{student_id}"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"edit_price_{student_id}"),
            types.InlineKeyboardButton(archive_btn_text, callback_data=archive_callback), # Вместо удаления
            types.InlineKeyboardButton("🔙 В профиль", callback_data=f"fast_view_{student_id}")
        )
        
        bot.edit_message_text(settings_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    # --- 4. СМЕНА ЦЕНЫ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price_"))
    @safe_handler(bot)
    def edit_price_init(call):
        student_id = call.data.split("_")[2]
        user_data[call.from_user.id] = {'step': 'waiting_new_price', 'edit_student_id': student_id}
        
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("🔙 Отмена", callback_data=f"edit_stu_{student_id}")
        )
        bot.edit_message_text("💰 <b>Введите новую цену (PLN):</b>", 
                            call.message.chat.id, call.message.message_id, 
                            reply_markup=markup, parse_mode="HTML")
        user_data[call.from_user.id]['last_instruction_id'] = call.message.message_id

    # --- 5. ДОБАВЛЕНИЕ УЧЕНИКА ---
    @bot.callback_query_handler(func=lambda call: call.data == "add_student")
    @safe_handler(bot)
    def add_student_init(call):
        user_id = call.from_user.id
        # Используем лоадинг как новое сообщение
        l_id = ui_refs['show_loading'](call.message.chat.id, "⌛ <b>Подготовка...</b>")
        
        user_data[user_id] = {'step': 'waiting_name'}
        ui_refs['clear_screen'](call.message.chat.id, keep_msg_id=l_id)
        
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_add"))
        bot.edit_message_text("📝 <b>Введите данные:</b>\n<code>@username Имя</code>", 
                            call.message.chat.id, l_id, parse_mode="HTML", reply_markup=markup)
        user_data[user_id]['last_instruction_id'] = l_id
    # --- 6. ЗАПРОС ПОДТВЕРЖДЕНИЯ УДАЛЕНИЯ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith(("archive_stu_", "restore_stu_")))
    @safe_handler(bot)
    def handle_archive_status(call):
        chat_id = call.message.chat.id
        data = call.data.split("_")
        action = data[0] # archive или restore
        student_id = data[2]

        new_status = 'inactive' if action == 'archive' else 'active'
        
        # ВЫЗОВ: Просто получаем результат (количество измененных строк)
        result = db.students.set_status(student_id, new_status)
        
        if result: # Если изменилась хотя бы 1 строка (True)
            alert_text = "📁 Ученик перенесен в архив" if action == 'archive' else "✅ Ученик восстановлен"
            bot.answer_callback_query(call.id, alert_text)
            
            # Возвращаемся в главное меню
            ui_refs['handle_start'](call.message)
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка: ученик не найден")
        
    # --- 8. РЕДАКТИРОВАНИЕ ИМЕНИ (Бесшовно) ---    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_name_"))
    @safe_handler(bot)
    def start_edit_name(call):
        user_id = call.from_user.id
        student_id = call.data.split("_")[2]

        # Устанавливаем состояние ожидания
        user_data[user_id] = {
            'step': 'waiting_edit_name',
            'edit_student_id': student_id
        }

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📝 <b>Введите новое имя ученика:</b>",
            parse_mode="HTML",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 Отмена", callback_data=f"edit_stu_{student_id}")
            )
        )
    @bot.callback_query_handler(func=lambda call: call.data == "calendar_full_view")
    @safe_handler(bot) # <-- ТЕПЕРЬ ВСЁ ПОД КОНТРОЛЕМ ЭТОЙ СТРОЧКИ
    def show_main_calendar(call):
        # Берем текущую дату
        now = datetime.now()
    
        # Генерируем календарь: 
        # student_id="all" (смотрим всех)
        # mode="view" (режим просмотра занятий)
        markup = create_calendar(
            student_id="all", 
            year=now.year, 
            month=now.month, 
            mode="view"
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🗓 <b>Общий график занятий</b>\n\nНиже представлена ваша загрузка. Дни с уроками помечены маркером 🔹. Нажмите на день для просмотра деталей.",
            reply_markup=markup,
            parse_mode="HTML"
        )
    # Ставим декоратор СРАЗУ под хендлером телеграма
    @bot.callback_query_handler(func=lambda call: call.data.startswith("all_cal_day_"))
    @safe_handler(bot) # <-- ТЕПЕРЬ ВСЁ ПОД КОНТРОЛЕМ ЭТОЙ СТРОЧКИ
    def show_all_lessons_on_day(call):
        # Разбираем callback
        params = call.data.split("_")
        year, month, day = params[3], params[4], params[5]
        date_str = f"{year}-{int(month):02d}-{int(day):02d}"

        query = """
            SELECT l.lesson_time, c.name 
            FROM lessons l
            JOIN contacts c ON l.student_id = c.id
            WHERE date(l.lesson_date) = date(?)
            ORDER BY l.lesson_time ASC
        """
    
        # Просто пишем логику. Если тут что-то упадет — декоратор поймает!
        lessons = db.execute(query, (date_str,), fetchall=True) or []

        text = f"🗓 <b>Занятия на {day}.{month}.{year}</b>\n"
        text += "──────────────────────────\n"

        if not lessons:
            text += "Записей не найдено."
        else:
            for res in lessons:
                # Твой BaseDB возвращает dict, берем по ключам:
                time_val = res.get('lesson_time', '--:--')
                name_val = res.get('name', 'Ученик')
                text += f"🕒 <code>{time_val}</code> — <b>{name_val}</b>\n"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 К календарю", callback_data=f"cal_nav_all_view_{year}_{month}"))
    
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                        reply_markup=markup, parse_mode="HTML")
    
# --- ВНЕШНИЕ ФУНКЦИИ ---

def handle_student_text(bot, db, message, user_data, ui_refs):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    
    parts = text.split()
    username = parts[0] if parts[0].startswith('@') else "None"
    name = " ".join(parts[1:]) if username != "None" and len(parts) > 1 else text.replace('@', '')

    db.students.add_contact(name, f"id_{int(time.time())}", None, chat_id, username)
    
    state = user_data.get(user_id, {})
    # Чистим инструкцию и сообщение пользователя
    try:
        bot.delete_message(chat_id, state.get('last_instruction_id'))
        bot.delete_message(chat_id, message.message_id)
    except: pass
    
    user_data[user_id]['step'] = None
    ui_refs['handle_start'](message)

def handle_price_update(bot, db, finance, message, user_id, student_id, user_data, ui_refs):
    chat_id = message.chat.id
    try:
        new_price = int(message.text.strip())
        state = user_data.get(user_id, {})
        
        # Удаляем ввод пользователя
        try: bot.delete_message(chat_id, message.message_id)
        except: pass

        current_balance = finance.get_actual_balance(student_id)
        if db.students.set_new_lesson_price(student_id, new_price, current_balance):
            student_data = db.students.get_by_id(student_id)
            # Редактируем старую инструкцию прямо в карточку (эффект мгновенного обновления)
            render_student_card(bot, chat_id, student_data, finance, is_search=True, edit_msg_id=state.get('last_instruction_id'))
            user_data[user_id]['step'] = None
    except:
        bot.send_message(chat_id, "⚠ Введите число!")

def handle_save_edited_name(bot, db, message, student_id, user_data, ui_refs, finance):
    chat_id = message.chat.id
    user_id = message.from_user.id
    new_name = message.text.strip()

    if not new_name:
        bot.send_message(chat_id, "⚠️ Имя не может быть пустым.")
        return

    try:
        # 1. Обновляем имя в БД
        db.students.set_new_name(student_id, new_name)

        # 2. Сбрасываем стейт (важно, чтобы бот перестал ждать имя)
        user_data[user_id] = {}

        # 3. Чистим сообщение пользователя
        try: bot.delete_message(chat_id, message.message_id)
        except: pass

        # 4. Обновляем основную карточку студента
        student_data = db.students.get_by_id(student_id)
        from view.student_render import render_student_card
        
        render_student_card(
            bot, 
            chat_id, 
            student_data, 
            finance, 
            is_search=True, # Чтобы была кнопка "Назад"
            edit_msg_id=ui_refs.get('welcome_msg_id')
        )
        
        # Можно отправить временное уведомление
        temp = bot.send_message(chat_id, f"✅ Имя изменено на <b>{new_name}</b>", parse_mode="HTML")
        threading.Timer(1, lambda: bot.delete_message(chat_id, temp.message_id)).start() # Удалим через 1 секунды
        # Через пару секунд можно его удалить, если хочешь идеальной чистоты

    except Exception as e:
        print(f"Error updating name: {e}")
        bot.send_message(chat_id, "❌ Не удалось изменить имя.")