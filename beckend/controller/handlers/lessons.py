import time
from telebot import types
from view.calendar_view import create_calendar
from helper.error_handler import safe_handler
def register_lesson_handlers(bot, db, ui_refs, finance):

    # --- 1. ОТКРЫТИЕ КАЛЕНДАРЯ (ЧИСТАЯ ТРАНСФОРМАЦИЯ) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_calendar_"))
    @safe_handler(bot)
    def lessons_cal(call):
        student_id = call.data.split("_")[2]
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        
        # 1. Мгновенный визуальный отклик (песочные часы в кнопке)
        bot.answer_callback_query(call.id, "📅 Открываю календарь...")
        
        # 2. Вместо удаления — превращаем текущее сообщение в лоадинг (опционально)
        # Но лучше сразу генерировать календарь, если база быстрая.
        # Если хочешь "мерцание" лоадинга, раскомментируй строку ниже:
        # bot.edit_message_text("📅 <b>Загрузка календаря...</b>", chat_id, message_id, parse_mode="HTML")
        
        try:
            # --- ВОТ ТУТ ДОБАВИЛИ ПОЛУЧЕНИЕ ОПЛАТ ---
            highlight_dates = db.payments.get_dates_by_student(student_id)
        
        # --- И ПЕРЕДАЕМ db=db ВМЕСТЕ С ОПЛАТАМИ ---
            markup = create_calendar(student_id, db=db, highlight_dates=highlight_dates)
            
            # 3. Редактируем сообщение: Профиль -> Календарь
            bot.edit_message_text(
                text="📅 <b>Выберите дату занятия:</b>",
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=markup,
                parse_mode="HTML",
            )
            
            # Обновляем ID главного сообщения, чтобы не терять его
            ui_refs['welcome_msg_id'] = message_id
            
        except Exception as e:
            print(f"❌ Ошибка при открытии календаря: {e}")
            bot.answer_callback_query(call.id, "⚠️ Ошибка при загрузке календаря", show_alert=True)

    # --- 2. ВЫБОР ДНЯ (СЕТКА ВРЕМЕНИ) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_day_"))
    @safe_handler(bot)
    def select_lesson_day(call):
        d = call.data.split("_")
        if len(d) < 6: return

        try:
            s_id = d[2]
            year, month, day = d[3], d[4].zfill(2), d[5].zfill(2)
            sel_date = f"{year}-{month}-{day}"
            display_date = f"{day}.{month}.{year}"

            # 1. Сначала уведомляем в полоске, что работаем
            bot.answer_callback_query(call.id, "Загружаю время...")

            # 2. Получаем данные
            booked = db.lessons.get_booked_by_date(sel_date) 
            
            booked_text = ""
            if booked:
                booked_text = "\n\n<b>Занято:</b>\n" + "\n".join(
                    [f"• {t} — {val['name']}" for t, val in booked.items()]
                )
            
            markup = types.InlineKeyboardMarkup(row_width=4)
            slots = [f"{h:02d}:00" for h in range(24)] 
            
            btns = []
            for t in slots:
                if t in booked:
                    data = booked[t]
                    if isinstance(data, str):
                        btns.append(types.InlineKeyboardButton(f"🔒 {t}", callback_data=f"inf_{data}"))
                        continue
                    if str(data.get('id')) == str(s_id):
                        btns.append(types.InlineKeyboardButton(f"❌ {t}", callback_data=f"del_les_{sel_date}_{t}_{s_id}"))
                    else:
                        owner = data.get('name', 'Ученик')
                        btns.append(types.InlineKeyboardButton(f"🔒 {t}", callback_data=f"inf_{owner}"))
                else:
                    btns.append(types.InlineKeyboardButton(t, callback_data=f"stme_{s_id}_{sel_date}_{t}"))
            
            markup.add(*btns)
            markup.add(types.InlineKeyboardButton("🔙 Назад к календарю", callback_data=f"open_calendar_{s_id}"))
            
            text = (
                f"📅 <b>Дата: {display_date}</b>\n"
                f"❌ — отмена твоего, 🔒 — занято другими.\n"
                f"{booked_text}"
            )

            # 3. Редактируем ТЕКУЩЕЕ сообщение (календарь превращается в сетку времени)
            bot.edit_message_text(
                text,
                call.message.chat.id, 
                call.message.message_id, 
                reply_markup=markup, 
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"❌ Ошибка в select_lesson_day: {e}")

    # --- 3. ЗАПИСЬ НА УРОК ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("stme_"))
    @safe_handler(bot)
    def save_lesson(call):
        d = call.data.split("_")
        student_id, lesson_date, lesson_time = d[1], d[2], d[3]
        
        # 1. Сохраняем в базу
        db.lessons.add(student_id, lesson_date, lesson_time, db.students)
        bot.answer_callback_query(call.id, f"✅ Записано на {lesson_time}")

        # 2. ПОЛУЧАЕМ ДАННЫЕ (нужны для рендера карточки)
        student_data = db.students.get_by_id(student_id)

        # 3. ВЫЗЫВАЕМ ОТРИСОВКУ КАРТОЧКИ (импортируй её в начале файла)
        from view.student_render import render_student_card
        
        render_student_card(
            bot, 
            call.message.chat.id, 
            student_data, 
            finance, 
            edit_msg_id=call.message.message_id # Редактируем текущее сообщение (сетку времени)
        )

    # --- 4. УДАЛЕНИЕ УРОКА (ОТМЕНА) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_les_"))
    @safe_handler(bot)
    def handle_delete_lesson(call):
        parts = call.data.split("_")
        # Извлекаем параметры из callback_data
        l_date, l_time, s_id = parts[2], parts[3], parts[4]

        # ВАЖНО: Добавляем False в конец, если твой метод принимает is_refund.
        # Если ты просто удалил строку с балансом в репозитории, то аргументы остаются прежними.
        # Но судя по твоей логике динамического расчета, баланс пересчитается сам 
        # на основе количества оставшихся уроков в БД.
        success, msg = db.lessons.delete(l_date, l_time, s_id, db.students)

        if success:
            bot.answer_callback_query(call.id, "🗑️ Занятие удалено из календаря")
        else:
            bot.answer_callback_query(call.id, f"⚠️ {msg}", show_alert=True)

        # Обновляем этот же экран времени, чтобы кнопка исчезла
        date_parts = l_date.split("-")
        call.data = f"cal_day_{s_id}_{date_parts[0]}_{date_parts[1]}_{date_parts[2]}"
        select_lesson_day(call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("start_lesson_"))
    @safe_handler(bot)
    def start_lesson_callback(call):
        chat_id = call.message.chat.id
        student_id = call.data.split("_")[2]
        student_name = db.students.get_by_id(student_id)['name']
        ui_refs['show_loading'](chat_id, "⌛ <b>Фиксирую урок...</b>", call=call)

        success, result = db.lessons.auto_lesson_check_in(student_id, db.students)
        student_data = db.students.get_by_id(student_id)

        if not success:
            # result теперь содержит либо имя того кто занял, либо инфу о повторе
            if "уже был урок" in result:
                msg = f"⚠️ У {student_name} {result}!"
            else:
                msg = f"⚠️ Сейчас идет урок у: {result}"
                
            bot.answer_callback_query(call.id, msg, show_alert=True)
            
            # Возвращаем карточку
            from view.student_render import render_student_card
            render_student_card(bot, chat_id, student_data, finance, edit_msg_id=call.message.message_id)
            return

        # --- ЛОГИКА ФОРМИРОВАНИЯ ССЫЛКИ (как в твоем рендере) ---
        phone = student_data.get('phone')
        username = student_data.get('username')
        
        # Определяем цель (приоритет телефону, если он не системный ID)
        target = phone if phone and not str(phone).startswith('id_') else (username if username and username != "None" else None)
        
        # Формируем URL чата
        chat_url = f"https://t.me/{str(target).replace('@', '').strip()}" if target else None

        # Формируем клавиатуру
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # Первый ряд: Meet и Написать
        btn_meet = types.InlineKeyboardButton("🔗 Meet", url="https://meet.google.com/new")
        if chat_url:
            btn_chat = types.InlineKeyboardButton("💬 Написать", url=chat_url)
        else:
            btn_chat = types.InlineKeyboardButton("💬 ———", callback_data="none")
            
        markup.row(btn_meet, btn_chat)
        
        # Второй ряд: возврат
        markup.row(types.InlineKeyboardButton("🔙 В профиль", callback_data=f"fast_view_{student_id}"))

        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"✅ <b>Урок зафиксирован!</b>\n──────────────────────────\n"
                f"👤 Ученик: <b>{student_data['name']}</b>\n"
                f"⏰ Время: <b>{result}</b>\n\n"
                f"<i>Урок списан. Ссылки на Meet и чат подготовлены.</i>",
            parse_mode="HTML", 
            reply_markup=markup
        )
        
        ui_refs['welcome_msg_id'] = call.message.message_id