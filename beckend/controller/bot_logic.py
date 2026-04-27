import time
from database.db_manager import db
from view.student_render import render_student_card
from controller.handlers.common import register_common_handlers
from controller.handlers.students import register_student_handlers, handle_student_text
from controller.handlers.payments import register_payment_handlers, handle_payment_text
from controller.handlers.lessons import register_lesson_handlers

user_data = {}
ui_refs = {
    'search_results_ids': [],
    'welcome_msg_id': None,
    'handle_start': None,
    'clear_screen': None
}

def register_handlers(bot, finance):
    
    def clear_screen(chat_id):
        if ui_refs['welcome_msg_id']:
            try: bot.delete_message(chat_id, ui_refs['welcome_msg_id'])
            except: pass
            ui_refs['welcome_msg_id'] = None
        for m_id in ui_refs['search_results_ids']:
            try: bot.delete_message(chat_id, m_id)
            except: pass
        ui_refs['search_results_ids'].clear()

    ui_refs['clear_screen'] = clear_screen

    # Регистрация Callback-обработчиков
    ui_refs['handle_start'] = register_common_handlers(bot, db, finance, user_data, ui_refs)
    register_student_handlers(bot, db, user_data, ui_refs)
    register_payment_handlers(bot, db, user_data, ui_refs)
    register_lesson_handlers(bot, db, ui_refs)

    # Единый обработчик текста
    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def handle_text(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        if message.text.startswith('/'): return

        state = user_data.get(user_id, {})
        step = state.get('step')

        # 1. Если ждем имя ученика
        if step == 'waiting_name':
            handle_student_text(bot, db, message, user_data, ui_refs)
        
        # 2. Если ждем сумму денег
        elif step == 'waiting_pay_amount':
            handle_payment_text(bot, db, message, user_data, ui_refs)
        
        # 3. Иначе — это ПОИСК
        else:
            results = db.search_contacts(message.text.strip())
            if results:
                clear_screen(chat_id)
                for r in results:
                    m_id = render_student_card(bot, chat_id, r, finance, is_search=True)
                    ui_refs['search_results_ids'].append(m_id)