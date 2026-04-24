import time
from telebot import types
from database.db_manager import db
from view.student_render import render_student_card, get_main_markup
from view.calendar_view import create_calendar
# Глобальные хранилища для управления сообщениями внутри сессии бота
search_results_ids = []
welcome_msg_id = None
user_data = {}

def register_handlers(bot, finance):
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        global search_results_ids, welcome_msg_id
        chat_id = message.chat.id
        
        # Чистим старое
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        if welcome_msg_id:
            try: bot.delete_message(chat_id, welcome_msg_id)
            except: pass
            welcome_msg_id = None

        for m_id in search_results_ids:
            try: bot.delete_message(chat_id, m_id)
            except: pass
        search_results_ids.clear()
        
        contacts = db.get_all()
        if not contacts:
            msg = bot.send_message(chat_id, "👋 <b>Список пуст.</b>", 
                                   parse_mode="HTML", reply_markup=get_main_markup())
            welcome_msg_id = msg.message_id
        else:
            for i, c in enumerate(contacts):
                is_last = (i == len(contacts) - 1)
                m_id = render_student_card(bot, chat_id, c, finance, show_add_button=is_last)
                search_results_ids.append(m_id)

    @bot.callback_query_handler(func=lambda call: call.data == "add_student")
    def start_manual_add(call):
        user_id = call.from_user.id
        user_data[user_id] = {'step': 'waiting_name'}
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_add"))
        msg = bot.send_message(call.message.chat.id, "📝 <b>Введите данные:</b> (@username Имя)", 
                               parse_mode="HTML", reply_markup=markup)
        user_data[user_id]['last_msg'] = msg.message_id
        # bot.register_next_step_handler и остальная логика добавления...

    @bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
    def handle_delete(call):
        s_id = call.data.split('_')[1]
        db.delete_contact(s_id)
        bot.answer_callback_query(call.id, "🗑️ Удалено")
        handle_start(call.message)

    @bot.message_handler(content_types=['text'])
    def handle_search(message):
        # Логика поиска с использованием render_student_card
        query = message.text.strip()
        results = db.search_contacts(query)
        if results:
            for r in results:
                render_student_card(bot, message.chat.id, r, finance, is_search=True)
                

		# 1. Открываем календарь
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_calendar_"))
    def open_cal(call):
        student_id = call.data.split("_")[2]
        # Удаляем список учеников, чтобы не мешался
        bot.delete_message(call.message.chat.id, call.message.message_id)
        
        markup = create_calendar(student_id)
        bot.send_message(call.message.chat.id, "📅 <b>Выберите дату занятия:</b>", 
                        reply_markup=markup, parse_mode="HTML")

    # 2. Ловим нажатие на день
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_day_"))
    def select_day(call):
        data = call.data.split("_")
        student_id, y, m, d = data[2], data[3], data[4], data[5]
        selected_date = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        
        # 1. Получаем словарь занятых слотов: {'время': 'имя'}
        booked_dict = db.get_booked_times_with_names(selected_date)
        
        # 2. Формируем текстовый список занятых уроков
        schedule_text = ""
        if booked_dict:
            schedule_text = "<b>📌 Расписание на этот день:</b>\n"
            # Сортируем по времени для порядка
            for t in sorted(booked_dict.keys()):
                schedule_text += f"• <code>{t}</code> — {booked_dict[t]}\n"
            schedule_text += "──────────────────\n"
        else:
            schedule_text = "<b>✨ Этот день пока свободен.</b>\n"

        markup = types.InlineKeyboardMarkup(row_width=4)
        available_slots = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", 
                           "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"]
        
        btns = []
        for t in available_slots:
            if t in booked_dict:
                # Если время занято (любым учеником)
                btn_text = f"🚫 {t}"
                callback = "ignore"
            else:
                btn_text = t
                callback = f"stme_{student_id}_{selected_date}_{t}"
            
            btns.append(types.InlineKeyboardButton(btn_text, callback_data=callback))
            
        markup.add(*btns)
        markup.add(types.InlineKeyboardButton("🔙 Назад к календарю", callback_data=f"open_calendar_{student_id}"))

        bot.edit_message_text(
            f"📅 Дата: <b>{selected_date}</b>\n\n"
            f"{schedule_text}"
            f"👇 Выберите свободное время:", 
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="HTML"
        )
    # 3. Финальное сохранение (ОТСТУП ВАЖЕН: на одном уровне с select_day)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("stme_"))
    def finalize_lesson(call):
        data = call.data.split("_")
        # stme_ID_DATE_TIME
        student_id = data[1]
        date_str = data[2]
        time_str = data[3]

        # Сохранение в БД
        res = db.add_lesson(student_id, date_str, time_str, "Урок", 60)

        if res:
            bot.answer_callback_query(call.id, "✅ Занятие успешно добавлено!")
        else:
            bot.answer_callback_query(call.id, "❌ Ошибка сохранения", show_alert=True)

        # Чистим сообщение выбора времени
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        # Возврат в главное меню
        handle_start(call.message)
        

		# 4. Обработка кнопки "Назад/Отмена" из календаря
    @bot.callback_query_handler(func=lambda call: call.data == "show_all")
    def back_to_menu(call):
        bot.answer_callback_query(call.id)
        # Чистим сообщение, в котором был календарь или время
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        # Вызываем handle_start, передавая message из колбэка
        handle_start(call.message)

    # 5. Обработка отмены при добавлении (если нужно)
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_add")
    def cancel_add_student(call):
        bot.answer_callback_query(call.id, "Отменено")
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass
        handle_start(call.message)