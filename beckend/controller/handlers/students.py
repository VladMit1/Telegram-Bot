import time
from telebot import types
from view.student_render import render_student_card

def register_student_handlers(bot, db, user_data, ui_refs, finance):

    @bot.callback_query_handler(func=lambda call: call.data == "add_student")
    def add_student_init(call):
        user_id = call.from_user.id
        user_data[user_id] = {'step': 'waiting_name'}
        ui_refs['clear_screen'](call.message.chat.id)
        
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_add"))
        sent_msg = bot.send_message(call.message.chat.id, "📝 <b>Введите данные:</b>\n<code>@username Имя</code>", 
                                    parse_mode="HTML", reply_markup=markup)
        user_data[user_id]['last_instruction_id'] = sent_msg.message_id
    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_stu_"))
    def open_card(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        student_id = int(call.data.split("_")[2])

        # 1. УДАЛЯЕМ СООБЩЕНИЕ НАСТРОЕК (или любое другое, где была нажата кнопка)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass

        # 2. Очищаем экран (твой существующий метод)
        ui_refs['clear_screen'](chat_id)

        # 3. Получаем данные и рендерим карточку
        student_data = db.get_student_by_id(student_id)

        if student_data:
            m_id = render_student_card(
                bot, 
                chat_id, 
                student_data, 
                finance, 
                is_search=True 
            )
            ui_refs['search_results_ids'].append(m_id)
        else:
            bot.answer_callback_query(call.id, "❌ Ученик не найден", show_alert=True)
    @bot.message_handler(regexp=r"^/id\d+")
    def handle_id_click(message):
        chat_id = message.chat.id
        student_id = int(message.text.replace("/id", ""))
    
        # 1. Удаляем команду /id123 из чата, чтобы не мусорить
        try: bot.delete_message(chat_id, message.message_id)
        except: pass

        # 2. Очищаем экран от списка (если у тебя так настроено)
        ui_refs['clear_screen'](chat_id)

        # 3. Достаем данные и показываем карточку
        student_data = db.get_student_by_id(student_id)
        if student_data:
            m_id = render_student_card(bot, chat_id, student_data, finance, is_search=True)
            ui_refs['search_results_ids'].append(m_id)
        else:
            bot.send_message(chat_id, "❌ Ошибка: ученик не найден.")

    @bot.callback_query_handler(func=lambda call: call.data == "show_all")
    def go_back_to_list(call):
        chat_id = call.message.chat.id
        # Очищаем карточку
        ui_refs['clear_screen'](chat_id)
    
        # Снова вызываем поиск или показываем всех (зависит от твоей логики)
        # Если хочешь просто показать всех:
        results = db.get_all_contacts() 
        from view.student_render import render_student_list
        m_id = render_student_list(bot, chat_id, results, finance)
        ui_refs['search_results_ids'].append(m_id)
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_stu_"))
    def student_settings(call):
        student_id = call.data.split("_")[2]
        # Получаем полные данные ученика
        student = db.get_student_by_id(student_id) 

        if not student:
            bot.answer_callback_query(call.id, "❌ Ученик не найден")
            return

        # Распаковываем нужные данные (индексы зависят от твоей БД, обычно: 0-id, 1-name, 7-price)
        # Предположим, цена урока лежит в student[7], а телефон в student[2]
        name = student[1]
        phone = student[2] if not str(student[2]).startswith('id_') else "Не указан"
        lesson_price = student[9] if len(student) > 9 else "Не задана"

        try: 
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except: 
            pass
        
        # Формируем информативный текст
        settings_text = (
            f"⚙️ <b>Настройки:</b> {name}\n"
            f"──────────────────────────\n"
            f"💰 <b>Текущая цена:</b> <code>{lesson_price} PLN</code>\n"
            f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
            f"──────────────────────────\n"
            f"<i>Выберите параметр для изменения:</i>"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🏷️ Изменить Имя", callback_data=f"edit_name_{student_id}"),
            types.InlineKeyboardButton("💰 Изменить Цену", callback_data=f"edit_price_{student_id}"),
            types.InlineKeyboardButton("🗑️ Удалить профиль", callback_data=f"confirm_delete_{student_id}"),
            types.InlineKeyboardButton("🔙 Назад к профилю", callback_data=f"view_stu_{student_id}")
        )
    
        bot.send_message(call.message.chat.id, settings_text, 
                     reply_markup=markup, parse_mode="HTML")
    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
    def confirm_delete_student(call):
        student_id = call.data.split("_")[2]

        # Вызываем наш метод с проверкой
        success, message = db.try_delete_student(student_id, finance)
    
        if success:
            # Если удалили — уведомляем и возвращаемся в список
            bot.answer_callback_query(call.id, message, show_alert=True)
            ui_refs['handle_start'](call.message) # Возврат в меню
        else:
            # Если долг — показываем алерт и НИЧЕГО не удаляем
            bot.answer_callback_query(call.id, message, show_alert=True)

    @bot.message_handler(content_types=['contact'])
    def handle_contact_object(message):
        chat_id = message.chat.id
        
        # Вытаскиваем данные из карточки
        phone = message.contact.phone_number
        first_name = message.contact.first_name
        last_name = message.contact.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        username = "None" # В карточке контакта username обычно не передается

        # Сохраняем в базу
        db.add_contact(full_name, phone, None, chat_id, username)
        
        # Сбрасываем шаги и обновляем экран
        user_id = message.from_user.id
        if user_id in user_data:
            user_data[user_id]['step'] = None
            
        # Возвращаемся на главный экран
        ui_refs['handle_start'](message)

def handle_student_text(bot, db, message, user_data, ui_refs):
    user_id = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()
    state = user_data.get(user_id, {})

    parts = text.split()
    username = parts[0] if parts[0].startswith('@') else "None"
    name = " ".join(parts[1:]) if username != "None" and len(parts) > 1 else text.replace('@', '')

    if username != "None" and db.search_contacts(username):
        err = bot.send_message(chat_id, f"⚠️ Ученик <b>{username}</b> уже есть!")
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        time.sleep(2)
        try: bot.delete_message(chat_id, err.message_id)
        except: pass
        return

    db.add_contact(name, f"id_{int(time.time())}", None, chat_id, username)
    if state.get('last_instruction_id'):
        try: bot.delete_message(chat_id, state['last_instruction_id'])
        except: pass
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    user_data[user_id]['step'] = None
    ui_refs['handle_start'](message)

    # Инициализация смены цены
    # Если ты передаешь его как user_data, используй его везде внутри этой функции
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price_"))
    def edit_price_init(call):
        student_id = call.data.split("_")[2]
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        # Удаляем меню настроек сразу
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        
        user_data[user_id] = {
            'step': 'waiting_new_price',
            'edit_student_id': student_id
        }
        
        sent_msg = bot.send_message(chat_id, "💰 <b>Введите новую цену за урок (PLN):</b>", parse_mode="HTML")
        # Сохраняем ID инструкции, чтобы потом её удалить
        user_data[user_id]['last_instruction_id'] = sent_msg.message_id
def handle_price_update(bot, db, finance, message, user_id, student_id, user_data, ui_refs):
    chat_id = message.chat.id
    try:
        new_price = int(message.text.strip())
        
        # 1. Логика БД
        current_balance = finance.get_actual_balance(student_id)
        success = db.set_new_lesson_price(student_id, new_price, current_balance)
        
        if success:
            state = user_data.get(user_id, {})
            
            # Удаляем сообщение-инструкцию "Введите новую цену..."
            if state.get('last_instruction_id'):
                try: bot.delete_message(chat_id, state['last_instruction_id'])
                except: pass
            
            # Удаляем сообщение пользователя с введённым числом
            try: bot.delete_message(chat_id, message.message_id)
            except: pass

            # Возвращаемся в карточку ученика, чтобы увидеть обновленную цену
            student_data = db.get_student_by_id(student_id)
            if student_data:
                render_student_card(bot, chat_id, student_data, finance, is_search=True)
            
            # Сбрасываем стейт
            user_data[user_id]['step'] = None
            
    except ValueError:
        bot.send_message(chat_id, "⚠ <b>Введите целое число!</b>", parse_mode="HTML")