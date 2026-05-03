import time
from telebot import types
from view.calendar_view import create_calendar

def register_lesson_handlers(bot, db, ui_refs, finance):

    # --- 1. ОТКРЫТИЕ КАЛЕНДАРЯ (С ЛОАДИНГОМ) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_calendar_"))
    def lessons_cal(call):
        student_id = call.data.split("_")[2]
        
        # Используем лоадинг (создаем новое сообщение, так как старое удалим)
        l_id = ui_refs['show_loading'](call.message.chat.id, "📅 <b>Загрузка календаря...</b>")
        
        ui_refs['clear_screen'](call.message.chat.id, keep_msg_id=l_id)
        
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        markup = create_calendar(student_id)
        
        # Редактируем заглушку лоадинга на сам календарь
        bot.edit_message_text(
            "📅 <b>Выберите дату занятия:</b>",
            chat_id=call.message.chat.id,
            message_id=l_id,
            reply_markup=markup,
            parse_mode="HTML"
        )
        ui_refs['welcome_msg_id'] = l_id

    # --- 2. ВЫБОР ДНЯ (СЕТКА ВРЕМЕНИ) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_day_"))
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
    def save_lesson(call):
        d = call.data.split("_")
        student_id, lesson_date, lesson_time = d[1], d[2], d[3]
        
        db.lessons.add(student_id, lesson_date, lesson_time, db.students)
        bot.answer_callback_query(call.id, f"✅ Записано на {lesson_time}")

        # Обновляем этот же экран времени без удаления (мгновенно появится крестик)
        select_lesson_day(call)

    # --- 4. УДАЛЕНИЕ УРОКА (ОТМЕНА) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_les_"))
    def handle_delete_lesson(call):
        parts = call.data.split("_")
        l_date, l_time, s_id = parts[2], parts[3], parts[4]

        success = db.lessons.delete(l_date, l_time, s_id, db.students)

        if success:
            bot.answer_callback_query(call.id, "🗑️ Занятие отменено")
        else:
            bot.answer_callback_query(call.id, "⚠️ Ошибка при отмене", show_alert=True)

        # Обновляем этот же экран времени
        date_parts = l_date.split("-")
        call.data = f"cal_day_{s_id}_{date_parts[0]}_{date_parts[1]}_{date_parts[2]}"
        select_lesson_day(call)

    # --- 5. БЫСТРЫЙ СТАРТ УРОКА (CHECK-IN) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("start_lesson_"))
    def start_lesson_callback(call):
        chat_id = call.message.chat.id
        student_id = call.data.split("_")[2]

        # Лоадинг (создаем новое)
        l_id = ui_refs['show_loading'](chat_id, "⌛ <b>Фиксирую урок...</b>")

        success, result = db.lessons.auto_lesson_check_in(student_id, db.students)

        if not success:
            try: bot.delete_message(chat_id, l_id)
            except: pass
            bot.answer_callback_query(call.id, f"⚠️ Сейчас идет урок у: {result}", show_alert=True)
            return 

        ui_refs['clear_screen'](chat_id, keep_msg_id=l_id)
        student_data = db.students.get_by_id(student_id)
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 В профиль", callback_data=f"fast_view_{student_id}"))

        # Превращаем лоадинг в подтверждение
        bot.edit_message_text(
            f"✅ <b>Урок зафиксирован!</b>\n👤 Ученик: <b>{student_data['name']}</b>\n⏰ Время: <b>{result}</b>",
            chat_id, l_id, parse_mode="HTML", reply_markup=markup
        )