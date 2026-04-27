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
        # Собираем данные: ID ученика и выбранную дату
        s_id, sel_date = d[2], f"{d[3]}-{d[4].zfill(2)}-{d[5].zfill(2)}"
        
        # Получаем словарь вида {'09:00': 'Имя Ученика', '11:00': 'Другой Ученик'}
        booked = db.get_booked_times_with_names(sel_date)
        
        # Формируем список занятого времени для текста
        booked_text = ""
        if booked:
            booked_text = "\n\n<b>Занято:</b>\n" + "\n".join([f"• {t} — {name}" for t, name in booked.items()])
        
        markup = types.InlineKeyboardMarkup(row_width=4)
        # Сетка доступных часов (можешь менять под себя)
        slots = ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"]
        
        btns = []
        for t in slots:
            if t in booked:
                # Если занято — кнопка-заглушка с крестиком
                btns.append(types.InlineKeyboardButton(f"❌ {t}", callback_data="ignore"))
            else:
                # Если свободно — рабочая кнопка
                btns.append(types.InlineKeyboardButton(t, callback_data=f"stme_{s_id}_{sel_date}_{t}"))
        
        markup.add(*btns)
        # Кнопка возврата в календарь
        markup.add(types.InlineKeyboardButton("🔙 Назад к календарю", callback_data=f"open_calendar_{s_id}"))
        
        # Красиво оформляем дату для вывода (из ГГГГ-ММ-ДД в ДД.ММ)
        display_date = f"{d[5]}.{d[4]}.{d[3]}"
        
        header = f"📅 <b>Дата: {display_date}</b>\nВыберите свободное время:{booked_text}"
        
        bot.edit_message_text(header, call.message.chat.id, call.message.message_id, 
                              reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("stme_"))
    def save_lesson(call):
        # Структура callback: stme_{s_id}_{sel_date}_{t}
        d = call.data.split("_")
        student_id = d[1]
        lesson_date = d[2]
        lesson_time = d[3]
        
        # Сохраняем в базу
        db.add_lesson(student_id, lesson_date, lesson_time)
        
        # Всплывающее уведомление сверху
        bot.answer_callback_query(call.id, f"✅ Записано на {lesson_time}", show_alert=False)
        
        # Возвращаемся в главное меню (или можно в карточку ученика)
        ui_refs['handle_start'](call.message)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("start_lesson_"))
    def start_lesson_callback(call):
        student_id = call.data.split("_")[2]
    
        # 1. Записываем/проверяем урок
        is_added, l_time = db.auto_lesson_check_in(student_id)
    
        # 2. Получаем свежие данные
        student_data = db.get_student_by_id(student_id) 
        
        # 3. Импортируем рендер (если он не импортирован выше)
        from view.student_render import render_student_card 
    
        # 4. Обновляем саму карточку (теперь finance доступен из аргументов выше)
        render_student_card(
            bot, 
            call.message.chat.id, 
            student_data, 
            finance, 
            is_edit=True, 
            message_id=call.message.message_id
        )

        # 5. Кнопка-ссылка
        meet_url = f"https://meet.google.com/lookup/lesson-{student_id}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 ВОЙТИ В GOOGLE MEET", url=meet_url))
        
        bot.send_message(call.message.chat.id, f"✅ Урок на {l_time} зафиксирован.\nНажмите кнопку для входа:", reply_markup=markup)
        bot.answer_callback_query(call.id)
