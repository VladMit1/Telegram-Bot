from telebot import types
from view.student_render import render_student_list, get_main_markup
from view.calendar_view import create_calendar

def register_common_handlers(bot, db, finance, user_data, ui_refs):
    
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_data[user_id] = {'step': None}
        
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        
        # Полная очистка экрана (удалит все старые сообщения бота)
        ui_refs['clear_screen'](chat_id)
        
        contacts = db.students.get_all()
        
        if not contacts:
            msg = bot.send_message(chat_id, "👋 <b>База пуста. Добавьте первого ученика:</b>", 
                                   parse_mode="HTML", reply_markup=get_main_markup())
            ui_refs['welcome_msg_id'] = msg.message_id
        else:
            # При /start шлем новое сообщение (потому что старых нет)
            m_id = render_student_list(bot, chat_id, contacts, finance)
            ui_refs['welcome_msg_id'] = m_id

    @bot.callback_query_handler(func=lambda call: call.data in ["show_all", "main_menu", "cancel_add", "cancel_pay"])
    def handle_back(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        user_id = call.from_user.id
    
        # 1. Сбрасываем стейт, чтобы текстовые хендлеры не перехватывали ввод
        if user_id in user_data:
            user_data[user_id]['step'] = None
    
        contacts = db.students.get_all()
    
        if not contacts:
            try:
                bot.edit_message_text(
                    text="👋 <b>База пуста. Добавьте первого ученика:</b>", 
                    chat_id=chat_id, 
                    message_id=call.message.message_id, 
                    reply_markup=get_main_markup(), 
                    parse_mode="HTML"
                )
                ui_refs['welcome_msg_id'] = call.message.message_id
            except:
                msg = bot.send_message(chat_id, "👋 <b>База пуста:</b>", reply_markup=get_main_markup(), parse_mode="HTML")
                ui_refs['welcome_msg_id'] = msg.message_id
        else:
            # 2. РЕДАКТИРУЕМ ТЕКУЩЕЕ (сообщение отмены/оплаты) в список
            m_id = render_student_list(
                bot, 
                chat_id, 
                contacts, 
                finance, 
                edit_msg_id=call.message.message_id
            )
            # Принудительно запоминаем этот ID как основной экран
            ui_refs['welcome_msg_id'] = m_id
            # Очищаем список поиска, так как мы вернулись в корень
            ui_refs['search_results_ids'] = []
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_nav_"))
    def handle_calendar_navigation(call):
        params = call.data.split("_")
        student_id = params[2]
        mode = params[3]
        year = int(params[4])
        month = int(params[5])

        highlight_dates = None
        if mode == "pay":
            highlight_dates = db.payments.get_dates_by_student(student_id)

        markup = create_calendar(
            student_id=student_id, 
            year=year, 
            month=month, 
            mode=mode, 
            highlight_dates=highlight_dates
        )

        text = "💳 <b>Финансовый календарь:</b>" if mode == "pay" else "📅 <b>Расписание занятий:</b>"

        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        except Exception:
            pass

    return handle_start