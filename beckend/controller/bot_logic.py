import time
from database.db_manager import db
from view.student_render import render_student_card
from controller.handlers.common import register_common_handlers
from controller.handlers.students import register_student_handlers, handle_student_text,handle_price_update, handle_save_edited_name
from controller.handlers.payments import register_payment_handlers, handle_payment_text
from controller.handlers.lessons import register_lesson_handlers
from view.student_render import render_student_list

user_data = {}
ui_refs = {
    'search_results_ids': [],
    'welcome_msg_id': None,
    'handle_start': None,
    'clear_screen': None
}

def register_handlers(bot, finance):
    
    # --- УНИВЕРСАЛЬНЫЙ ЛОАДИНГ ---
    def show_loading(chat_id, text="⌛ <b>Загрузка...</b>", call=None):
        """
        Если передан call, редактирует старое сообщение (без прыжков).
        Если call нет, шлет новое сообщение.
        """
        if call:
            try:
                bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="HTML")
                return call.message.message_id
            except: pass
        
        # Если редактирование не вышло или это новый процесс
        msg = bot.send_message(chat_id, text, parse_mode="HTML")
        return msg.message_id


    # --- УНИВЕРСАЛЬНЫЙ ОЧИСТКА ЭКРАНА ---
    def clear_screen(chat_id, keep_msg_id=None):
        # Удаляем приветствие, если оно не является "якорем"
        if ui_refs['welcome_msg_id'] and ui_refs['welcome_msg_id'] != keep_msg_id:
            try: bot.delete_message(chat_id, ui_refs['welcome_msg_id'])
            except: pass
            ui_refs['welcome_msg_id'] = None

        # Удаляем все карточки из поиска, кроме "якоря"
        new_results = []
        for m_id in ui_refs['search_results_ids']:
            if m_id == keep_msg_id:
                new_results.append(m_id)
            else:
                try: bot.delete_message(chat_id, m_id)
                except: pass
        ui_refs['search_results_ids'] = new_results


    ui_refs['show_loading'] = show_loading
    ui_refs['clear_screen'] = clear_screen
    # Регистрация Callback-обработчиков
    ui_refs['handle_start'] = register_common_handlers(bot, db, finance, user_data, ui_refs)
    register_student_handlers(bot, db, user_data, ui_refs, finance)
    register_payment_handlers(bot, db, user_data, ui_refs, finance)
    register_lesson_handlers(bot, db,ui_refs, finance)

    # Единый обработчик текста (с авто-чисткой мусора)
    @bot.message_handler(func=lambda m: True, content_types=['text', 'photo', 'voice', 'sticker'])
    def handle_text(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Команды (/start, /id1 и т.д.) не трогаем — их обрабатывают другие хэндлеры
        if message.text and message.text.startswith('/'): 
            return

        state = user_data.get(user_id, {})
        step = state.get('step')

        # 1. Если ждем имя ученика
        if step == 'waiting_name':
            handle_student_text(bot, db, message, user_data, ui_refs)
        
        # 2. Если ждем сумму денег
        elif step == 'waiting_pay_amount':
            handle_payment_text(bot, db, message, user_data, ui_refs, finance)
            
        # 3. Если ждем новую цену (Маяк)
        elif step == 'waiting_new_price':
            handle_price_update(bot, db, finance, message, user_id, state.get('edit_student_id'), user_data, ui_refs)

        # 3.5 Если ждем новое имя ученика
        elif step == 'waiting_edit_name':
            student_id = state.get('edit_student_id')
            handle_save_edited_name(bot, db, message, student_id, user_data, ui_refs, finance)

        # 4. ПОИСК / ОБРАБОТКА СЛУЧАЙНОГО ТЕКСТА
        else:
            text_query = message.text.strip() if message.text else ""

            # 4.1 Пробуем найти ученика по введенному тексту
            results = db.students.search(text_query) if text_query else []
            
            if results:
                # Очищаем экран от предыдущих списков/карточек
                clear_screen(chat_id)
                
                # Рендерим список совпадений
                m_id = render_student_list(bot, chat_id, results, finance, edit_msg_id=ui_refs['welcome_msg_id'])
                
                ui_refs['search_results_ids'].append(m_id)
                
                # Удаляем сам поиск пользователя ("Влад"), чтобы чат был чистым
                try: bot.delete_message(chat_id, message.message_id)
                except: pass

            else:
                # 4.2 ЕСЛИ УЧЕНИК НЕ НАЙДЕН ИЛИ НАПИСАН БЕССМЫСЛЕННЫЙ ТЕКСТ (Например, во время урока)
                
                # 1. Мгновенно удаляем текст репетитора
                try: bot.delete_message(chat_id, message.message_id)
                except: pass

                # 2. Показываем короткую самосгорающую вспышку
                warn_msg = bot.send_message(
                    chat_id, 
                    "⚠️ <b>Ученик не найден / Ввод текста недоступен.</b>\n"
                    "<i>Не пишите сюда сообщения ученику — он их не видит! Используйте кнопку «💬 Написать».</i>",
                    parse_mode="HTML"
                )

                # 3. Удаляем предупреждение через 3.5 секунды (отдельный поток, чтобы бот не замирал)
                import threading
                def auto_delete():
                    time.sleep(3.5)
                    try: bot.delete_message(chat_id, warn_msg.message_id)
                    except: pass

                threading.Thread(target=auto_delete, daemon=True).start()