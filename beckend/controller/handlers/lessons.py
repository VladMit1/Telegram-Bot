from telebot import types
from view.calendar_view import create_calendar
def register_lesson_handlers(bot, db, ui_refs, finance):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_calendar_"))
    def lessons_cal(call):
        student_id = call.data.split("_")[2]
        ui_refs['clear_screen'](call.message.chat.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        markup = create_calendar(student_id)
        bot.send_message(call.message.chat.id, "📅 <b>Расписание:</b>", 
                        reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_day_"))
    def select_lesson_day(call):
        d = call.data.split("_")
        
        # ПРОВЕРКА: Если в списке меньше 6 элементов, значит это не клик по дате
        if len(d) < 6:
            print(f"⚠️ Неверный формат колбэка: {call.data}")
            return

        try:
            # Извлекаем данные
            s_id = d[2]
            year = d[3]
            month = d[4].zfill(2)
            day = d[5].zfill(2)
            
            sel_date = f"{year}-{month}-{day}"
            display_date = f"{day}.{month}.{year}"

            # 1. Получаем детали из базы
            booked = db.lessons.get_booked_by_date(sel_date) 
            # 2. Формируем текст занятых слотов
            booked_text = ""
            if booked:
                booked_text = "\n\n<b>Занято:</b>\n" + "\n".join(
                    [f"• {t} — {val['name']}" for t, val in booked.items()]
                )
            
            # 3. Сетка кнопок
            markup = types.InlineKeyboardMarkup(row_width=4)
            slots = [f"{h:02d}:00" for h in range(24)] # Генерация 00:00 - 23:00
            
            btns = []
            for t in slots:
                if t in booked:
                    data = booked[t]
                    
                    # Если в базе старый формат (просто строка)
                    if isinstance(data, str):
                        btns.append(types.InlineKeyboardButton(f"🔒 {t}", callback_data=f"inf_{data}"))
                        continue

                    # Проверка: мой урок или чужой
                    if str(data.get('id')) == str(s_id):
                        # Отмена своего урока
                        btns.append(types.InlineKeyboardButton(f"❌ {t}", callback_data=f"del_les_{sel_date}_{t}_{s_id}"))
                    else:
                        # Замок на чужой
                        owner = data.get('name', 'Ученик')
                        btns.append(types.InlineKeyboardButton(f"🔒 {t}", callback_data=f"inf_{owner}"))
                else:
                    # Свободное время
                    btns.append(types.InlineKeyboardButton(t, callback_data=f"stme_{s_id}_{sel_date}_{t}"))
            
            markup.add(*btns)
            markup.add(types.InlineKeyboardButton("🔙 Назад к календарю", callback_data=f"open_calendar_{s_id}"))
            
            text = (
                f"📅 <b>Дата: {display_date}</b>\n"
                f"❌ — отмена твоего, 🔒 — занято другими.\n"
                f"{booked_text}"
            )

            bot.edit_message_text(
                text,
                call.message.chat.id, 
                call.message.message_id, 
                reply_markup=markup, 
                parse_mode="HTML"
            )

        except Exception as e:
            print(f"❌ Ошибка в select_lesson_day: {e}")
            bot.answer_callback_query(call.id, "Ошибка при загрузке дня.")
    @bot.callback_query_handler(func=lambda call: call.data.startswith("stme_"))
    def save_lesson(call):
        d = call.data.split("_")
        student_id, lesson_date, lesson_time = d[1], d[2], d[3]
        
        # Мы обращаемся к репозиторию lessons и его методу add
        db.lessons.add(student_id, lesson_date, lesson_time, db.students)
        bot.answer_callback_query(call.id, f"✅ Записано на {lesson_time}")

        # Вместо handle_start попробуй просто обновить текущий экран времени, 
        # чтобы сразу увидеть появившийся красный крестик
        select_lesson_day(call)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("start_lesson_"))
    def start_lesson_callback(call):
        chat_id = call.message.chat.id
        student_id = call.data.split("_")[2]

        # 1. Фиксируем урок
        success, result = db.lessons.auto_lesson_check_in(student_id, db.students)

        if not success:
            bot.answer_callback_query(call.id, f"⚠️ Сейчас идет урок у: {result}", show_alert=True)
            return 

        # 2. ПОЛНАЯ ОЧИСТКА ЭКРАНА
        ui_refs['clear_screen'](chat_id)
    
        # 3. Достаем имя ученика для заголовка
        student_data = db.students.get_by_id(student_id)
        student_name = student_data['name'] 

        # 4. СОЗДАЕМ ШИРОКИЙ ЭКРАН УРОКА
        w = "⠀" # Невидимый расширитель
        meet_url = f"https://meet.google.com/lookup/lesson-{student_id}"
    
        markup = types.InlineKeyboardMarkup(row_width=1)
    
        # Делаем кнопки широкими для телефона
        btn_meet = types.InlineKeyboardButton(f"{w*5}🌐 ВОЙТИ В GOOGLE MEET{w*5}", url=meet_url)
        btn_back = types.InlineKeyboardButton(f"{w*7}🔙 НАЗАД К ПРОФИЛЮ{w*7}", callback_data=f"view_stu_{student_id}")

        markup.add(btn_meet, btn_back)

        # 5. Красивый текст-карточка
        text = (
            f"✅ <b>Урок зафиксирован!</b>\n"
            f"──────────────────────────\n"
            f"👤 Ученик: <b>{student_name}</b>\n"
            f"⏰ Время: <b>{result}</b>\n"
            f"──────────────────────────\n"
            f"<i>Ссылка готова. После урока нажмите\n«Назад», чтобы проверить баланс.</i>"
        )

        bot.send_message(
            chat_id, 
            text, 
            parse_mode="HTML", 
            reply_markup=markup
        )
        bot.answer_callback_query(call.id)
    @bot.callback_query_handler(func=lambda call: call.data == "delete_this_msg")
    def handle_delete_msg(call):
        try:
            # Просто удаляем само сообщение, где была кнопка "Закрыть"
            bot.delete_message(call.message.chat.id, call.message.message_id)
            
            # Обязательно отвечаем телеграму, чтобы кнопка не "зависала" в режиме загрузки
            bot.answer_callback_query(call.id)
        except Exception as e:
            # Если вдруг сообщение уже удалено (например, вручную), просто закрываем запрос
            bot.answer_callback_query(call.id)
            
    @bot.callback_query_handler(func=lambda call: call.data == "ignore")
    def handle_ignore(call):
        """Обработка нажатия на занятое время (крестик)"""
        bot.answer_callback_query(call.id, "⚠️ Это время уже занято другим учеником", show_alert=False)
    

    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_les_"))
    def handle_delete_lesson(call):
        # Разбираем callback: del_les_{date}_{time}_{s_id}
        # Пример: del_les_2026-05-02_09:00_5
        parts = call.data.split("_")
        l_date = parts[2]
        l_time = parts[3]
        s_id = parts[4]

        # 1. Удаляем из базы
        success = db.lessons.delete(l_date, l_time, s_id, db.students)

        if success:
            bot.answer_callback_query(call.id, "🗑️ Занятие отменено, баланс пополнен")
        else:
            bot.answer_callback_query(call.id, "⚠️ Ошибка при отмене", show_alert=True)

        # 2. Обновляем экран (перерисовываем кнопки времени)
        # Формируем данные для вызова select_lesson_day заново
        # Нам нужно превратить дату обратно в формат с подчеркиваниями для d[3], d[4], d[5]
        date_parts = l_date.split("-")
        call.data = f"cal_day_{s_id}_{date_parts[0]}_{date_parts[1]}_{date_parts[2]}"

        # Вызываем функцию выбора дня, чтобы обновить интерфейс
        select_lesson_day(call)