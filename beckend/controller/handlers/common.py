from telebot import types
from view.student_render import render_student_card, get_main_markup

def register_common_handlers(bot, db, finance, state_data, ui_refs):
    
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        state_data[user_id] = {'step': None}
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        
        # Очистка через центральную функцию
        ui_refs['clear_screen'](chat_id)
        
        contacts = db.get_all()
        if not contacts:
            msg = bot.send_message(chat_id, "👋 <b>Список пуст.</b>", 
                                   parse_mode="HTML", reply_markup=get_main_markup())
            ui_refs['welcome_msg_id'] = msg.message_id
        else:
            msg = bot.send_message(chat_id, "🗂 <b>Ваши ученики:</b>", parse_mode="HTML")
            ui_refs['welcome_msg_id'] = msg.message_id
            for i, c in enumerate(contacts):
                is_last = (i == len(contacts) - 1)
                m_id = render_student_card(bot, chat_id, c, finance, show_add_button=is_last)
                ui_refs['search_results_ids'].append(m_id)

    @bot.callback_query_handler(func=lambda call: call.data in ["show_all", "cancel_add", "cancel_pay"])
    def handle_back(call):
        user_id = call.from_user.id
        if user_id in state_data:
            state_data[user_id]['step'] = None
        handle_start(call.message)

    return handle_start  # Возвращаем функцию для внешнего вызова