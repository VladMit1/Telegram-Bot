import time
from telebot import types

def register_student_handlers(bot, db, state_data, ui_refs):

    @bot.callback_query_handler(func=lambda call: call.data == "add_student")
    def add_student_init(call):
        user_id = call.from_user.id
        state_data[user_id] = {'step': 'waiting_name'}
        ui_refs['clear_screen'](call.message.chat.id)
        
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_add"))
        sent_msg = bot.send_message(call.message.chat.id, "📝 <b>Введите данные:</b>\n<code>@username Имя</code>", 
                                    parse_mode="HTML", reply_markup=markup)
        state_data[user_id]['last_instruction_id'] = sent_msg.message_id

    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_stu_"))
    def student_settings(call):
        student_id = call.data.split("_")[2]
        student = db.get_student_by_id(student_id)
        ui_refs['clear_screen'](call.message.chat.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🏷️ Имя", callback_data=f"edit_name_{student_id}"),
            types.InlineKeyboardButton("💰 Цена", callback_data=f"edit_price_{student_id}"),
            types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_{student_id}"),
            types.InlineKeyboardButton("🔙 Назад", callback_data="show_all")
        )
        bot.send_message(call.message.chat.id, f"⚙️ <b>Настройки:</b> {student[1]}", 
                         reply_markup=markup, parse_mode="HTML")
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price_"))
    def edit_price_init(call):
        student_id = call.data.split("_")[2]
        user_id = call.from_user.id
        
        state_data[user_id] = {
            'step': 'waiting_new_price',
            'edit_student_id': student_id
        }
        
        bot.send_message(call.message.chat.id, "💰 <b>Введите новую цену за урок (PLN):</b>", parse_mode="HTML")
    @bot.callback_query_handler(func=lambda call: call.data.startswith('del_'))
    def delete_student(call):
        db.delete_contact(call.data.split('_')[1])
        bot.answer_callback_query(call.id, "🗑️ Удалено")
        ui_refs['handle_start'](call.message)

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
        if user_id in state_data:
            state_data[user_id]['step'] = None
            
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
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_price_"))
    def edit_price_init(call):
        student_id = call.data.split("_")[2]
        user_id = call.from_user.id
    
        user_data[user_id] = {
        'step': 'waiting_new_price',
        'edit_student_id': student_id
        }
    
        bot.send_message(call.message.chat.id, "💰 <b>Введите новую цену за урок (PLN):</b>", parse_mode="HTML")

# Обработка ввода новой цены (в handle_student_text или отдельном хендлере)

def handle_price_update(bot, db, finance, message, user_id, student_id, user_data, ui_refs):
    chat_id = message.chat.id
    try:
        # Пытаемся получить число
        new_price = int(message.text.strip())
        
        # 1. Считаем текущий баланс ДО изменения цены (Маяк)
        current_balance = finance.get_actual_balance(student_id)
        
        # 2. Сохраняем в базу (новую цену, дату и замороженный баланс)
        success = db.set_new_lesson_price(student_id, new_price, current_balance)
        
        if success:
            # Удаляем сообщение с вводом и инструкцию
            state = user_data.get(user_id, {})
            if state.get('last_instruction_id'):
                try: bot.delete_message(chat_id, state['last_instruction_id'])
                except: pass
            try: bot.delete_message(chat_id, message.message_id)
            except: pass

            bot.answer_callback_query(user_id, "✅ Цена и баланс обновлены", show_alert=False)
            
            # Сбрасываем стейт и возвращаемся в главное меню
            user_data[user_id]['step'] = None
            ui_refs['handle_start'](message)
        else:
            bot.send_message(chat_id, "❌ Ошибка БД.")
            
    except ValueError:
        msg = bot.send_message(chat_id, "⚠ <b>Введите целое число!</b>", parse_mode="HTML")
        # Можно добавить удаление этого предупреждения через пару секунд