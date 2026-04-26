import time
from datetime import datetime
from telebot import types
from database.db_manager import db
from view.student_render import render_student_card, get_main_markup
from view.calendar_view import create_calendar

# Глобальные хранилища
search_results_ids = []
welcome_msg_id = None
user_data = {}

def register_handlers(bot, finance):

    # --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОЧИСТКИ ---
    def clear_screen(chat_id):
        global search_results_ids, welcome_msg_id
        # Удаляем старый заголовок/приветствие
        if welcome_msg_id:
            try: bot.delete_message(chat_id, welcome_msg_id)
            except: pass
            welcome_msg_id = None
        # Удаляем все карточки учеников
        for m_id in search_results_ids:
            try: bot.delete_message(chat_id, m_id)
            except: pass
        search_results_ids.clear()

    # --- 1. КОМАНДА СТАРТ ---
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        global welcome_msg_id
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        user_data[user_id] = {'step': None}
        try: bot.delete_message(chat_id, message.message_id)
        except: pass
        
        clear_screen(chat_id)
        
        contacts = db.get_all()
        if not contacts:
            msg = bot.send_message(chat_id, "👋 <b>Список пуст.</b>", 
                                   parse_mode="HTML", reply_markup=get_main_markup())
            welcome_msg_id = msg.message_id
        else:
            msg = bot.send_message(chat_id, "🗂 <b>Ваши ученики:</b>", parse_mode="HTML")
            welcome_msg_id = msg.message_id
            for i, c in enumerate(contacts):
                is_last = (i == len(contacts) - 1)
                m_id = render_student_card(bot, chat_id, c, finance, show_add_button=is_last)
                search_results_ids.append(m_id)

    # --- 2. ОБРАБОТКА ТЕКСТА (ДОБАВЛЕНИЕ И ПОИСК) ---
    @bot.message_handler(func=lambda m: True, content_types=['text'])
    def handle_text(message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        if message.text.startswith('/'): return

        state = user_data.get(user_id, {})

        # Если мы ждем имя для добавления
        if state.get('step') == 'waiting_name':
            text = message.text.strip()
            
            # РАЗБИРАЕМСЯ С USERNAME
            parts = text.split()
            username = "None"
            name = text # По умолчанию всё сообщение — это имя

            # Если первое слово начинается с @
            if parts[0].startswith('@'):
                username = parts[0]
                # Если после @ есть еще слова, то они — имя. 
                # Если нет — имя будет таким же, как ник (но без @)
                if len(parts) > 1:
                    name = " ".join(parts[1:])
                else:
                    name = parts[0].replace('@', '') 
            
            # --- ПРОВЕРКА НА ДУБЛИКАТ ---
            if username != "None":
                # Ищем в базе, есть ли уже такой username
                existing = db.search_contacts(username)
                if existing:
                    # 1. Уведомляем об ошибке
                    error_msg = bot.send_message(chat_id, f"⚠️ Ученик <b>   {username}</b> уже есть!")
                    # 2. Удаляем сообщение пользователя, которое не прошло проверку
                    try: bot.delete_message(chat_id, message.message_id)
                    except: pass
                    # 3. Удаляем уведомление об ошибке через 2 секунды, чтобы не мусорить
                    time.sleep(2)
                    try: bot.delete_message(chat_id, error_msg.message_id)
                    except: pass
                    # Мы НЕ сбрасываем step, чтобы пользователь мог попробовать ввести другое имя
                    return
            # --- ДОБАВЛЕНИЕ В БАЗУ ---
            # Генерируем уникальный ID для телефона
            phone = f"id_{int(time.time())}"
            
            # Сохраняем в базу
            db.add_contact(name, phone, None, chat_id, username)
            
            # УДАЛЯЕМ ИНСТРУКЦИЮ
            instr_id = state.get('last_instruction_id')
            if instr_id:
                try: bot.delete_message(chat_id, instr_id)
                except: pass
            
            # УДАЛЯЕМ СООБЩЕНИЕ ПОЛЬЗОВАТЕЛЯ (то, что он ввел)
            try: bot.delete_message(chat_id, message.message_id)
            except: pass

            # Сбрасываем шаг и обновляем меню
            user_data[user_id]['step'] = None
            handle_start(message)
            return
        
        # Если ждем сумму пополнения
        if state.get('step') == 'waiting_pay_amount':
            amount_text = message.text.strip()
            student_id = state.get('student_id')
            pay_date = state.get('pay_date')
            instr_id = state.get('pay_instruction_id')

            # 1. Сразу удаляем сообщение пользователя (его цифры)
            try: bot.delete_message(chat_id, message.message_id)
            except: pass

            # 2. Сразу удаляем инструкцию бота ("Введите сумму")
            if instr_id:
                try: bot.delete_message(chat_id, instr_id)
                except: pass
            if amount_text.isdigit():
                amount = int(amount_text)
                db.add_payment(student_id, amount, pay_date)
                
                # Показываем чек
                temp_msg = bot.send_message(chat_id, f"✅ Баланс пополнен на {amount}!")
                
                user_data[user_id]['step'] = None
                handle_start(message) # Рисуем основной список
                
                # Удаляем чек через 3 секунды (вот тут sleep допустим, т.к. действие завершено)
                time.sleep(3)
                try: bot.delete_message(chat_id, temp_msg.message_id)
                except: pass
            else:
                # Если ввел не число - ругаемся и просим заново
                error_msg = bot.send_message(chat_id, "❌ Ошибка! Введите только число (например 500).")
                time.sleep(2)
                try: bot.delete_message(chat_id, error_msg.message_id)
                except: pass
                # Мы НЕ сбрасываем step, чтобы юзер мог исправиться
            return

        # Если это просто текст — ПОИСК
        results = db.search_contacts(message.text.strip())
        if results:
            clear_screen(chat_id)
            for r in results:
                m_id = render_student_card(bot, chat_id, r, finance, is_search=True)
                search_results_ids.append(m_id)

    # --- ОБРАБОТКА ПРИСЛАННОГО КОНТАКТА ---
    @bot.message_handler(content_types=['contact'])
    def handle_contact_object(message):
        chat_id = message.chat.id
        
        # Вытаскиваем данные из визитки
        phone = message.contact.phone_number
        first_name = message.contact.first_name
        last_name = message.contact.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        username = "None" # В объекте контакта юзернейм обычно не передается

        # Сохраняем в базу по твоей структуре:
        # (name, phone, photo_id, chat_id, username)
        db.add_contact(full_name, phone, None, chat_id, username)
        
        handle_start(message)



    # --- 3. ОБРАБОТКА КНОПОК (CALLBACKS) ---
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callbacks(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id

        # Нажали "Добавить"
        if call.data == "add_student":
            user_data[user_id] = {'step': 'waiting_name'}
            clear_screen(chat_id)
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            
            markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_add"))
            sent_msg = bot.send_message(chat_id, "📝 <b>Введите данные:</b>\n<code>@username Имя</code>", 
                             parse_mode="HTML", reply_markup=markup)
            user_data[user_id]['last_instruction_id'] = sent_msg.message_id
        # Открыли календарь
        elif call.data.startswith("open_calendar_"):
            student_id = call.data.split("_")[2]
            clear_screen(chat_id)
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            
            markup = create_calendar(student_id)
            bot.send_message(chat_id, "📅 <b>Выберите дату:</b>", reply_markup=markup, parse_mode="HTML")

        # Выбрали день
        elif call.data.startswith("cal_day_"):
            d = call.data.split("_")
            s_id, sel_date = d[2], f"{d[3]}-{d[4].zfill(2)}-{d[5].zfill(2)}"
            booked = db.get_booked_times_with_names(sel_date)
            
            markup = types.InlineKeyboardMarkup(row_width=4)
            slots = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
            btns = [types.InlineKeyboardButton(f"🚫 {t}" if t in booked else t, 
                    callback_data="ignore" if t in booked else f"stme_{s_id}_{sel_date}_{t}") for t in slots]
            markup.add(*btns).add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"open_calendar_{s_id}"))
            bot.edit_message_text(f"📅 <b>{sel_date}</b>", chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

        # Сохранение занятия
        elif call.data.startswith("stme_"):
            d = call.data.split("_")
            db.add_lesson(d[1], d[2], d[3])
            bot.answer_callback_query(call.id, "✅ Добавлено")
            handle_start(call.message)

        # Удаление ученика
        elif call.data.startswith('del_'):
            db.delete_contact(call.data.split('_')[1])
            handle_start(call.message)

        # Назад/Отмена
        elif call.data in ["show_all", "cancel_add"]:
            user_data[user_id] = {'step': None}
            handle_start(call.message)

        ## Кнопка "Настройки" (edit_stu_{id})
        elif call.data.startswith("edit_stu_"):
            student_id = call.data.split("_")[2]
            student = db.get_by_id(student_id)
            if not student: return

            # 1. ПОЛНАЯ ОЧИСТКА ЭКРАНА
            # Удаляем заголовок "Ваши ученики" и все остальные карточки
            clear_screen(chat_id)
            
            # 2. Удаляем саму карточку, с которой перешли в настройки
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass

            # 3. Создаем меню настроек
            markup = types.InlineKeyboardMarkup(row_width=2)
            markup.add(
                types.InlineKeyboardButton("🏷️ Изменить имя", callback_data=f"edit_name_{student_id}"),
                types.InlineKeyboardButton("💰 Изменить цену", callback_data=f"edit_prc_{student_id}")
            )
            markup.add(
                types.InlineKeyboardButton("🗑️ Удалить ученика", callback_data=f"del_{student_id}")
            )
            markup.add(types.InlineKeyboardButton("🔙 Назад к списку", callback_data="show_all"))

            # 4. Отправляем НОВОЕ чистое сообщение настроек
            text = f"⚙️ <b>Настройки ученика:</b> {student[1]}\n\nВыберите нужный пункт меню или вернитесь назад."
            
            sent_msg = bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
            
            # (Опционально) можно сохранить ID этого сообщения, если захочешь его потом тоже удалять
            user_data[user_id]['last_instruction_id'] = sent_msg.message_id

        # Кнопка "Отмена" в процессе оплаты
        elif call.data == "cancel_pay":
            # Просто сбрасываем шаг и возвращаемся в меню
            user_data[user_id]['step'] = None
            handle_start(call.message)
        # Кнопка "Пополнить" (pay_{id})
        # --- ВНУТРИ handle_callbacks ---
        elif call.data.startswith("pay_date_"):
            params = call.data.split("_")
            s_id = params[2]    # ID ученика
            sel_date = params[3] # Дата (например 2026-04-26)
            
            # Устанавливаем состояние ожидания суммы
            user_data[user_id]['step'] = 'waiting_pay_amount'
            user_data[user_id]['student_id'] = s_id
            user_data[user_id]['pay_date'] = sel_date
            
            # Удаляем календарь, чтобы он не висел
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
            
            # Создаем кнопку отмены
            markup = types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_pay")
            )
            
            # Спрашиваем сумму
            sent_msg = bot.send_message(
                chat_id, 
                f"💰 <b>Дата платежа: {sel_date}</b>\n\nВведите сумму пополнения:", 
                parse_mode="HTML", 
                reply_markup=markup
            )
            # Сохраняем ID сообщения, чтобы удалить его позже
            user_data[user_id]['pay_instruction_id'] = sent_msg.message_id
        # 1. Нажали кнопку "Пополнить" в карточке
        elif call.data.startswith("pay_"):
            student_id = call.data.split("_")[1]
    
            # Получаем даты оплат из базы для монеток
            pay_dates = db.get_payment_dates(student_id)
    
            # Генерируем календарь в режиме "pay"
            markup = create_calendar(student_id, mode="pay",        highlight_dates=pay_dates)
    
            # Очищаем экран и показываем календарь
            clear_screen(chat_id)
            try: bot.delete_message(chat_id, call.message.message_id)
            except: pass
    
            bot.send_message(chat_id, "💳 <b>Финансовый календарь</b>\nВыберите дату платежа (💰 — дни оплат):", 
                             reply_markup=markup, parse_mode="HTML")