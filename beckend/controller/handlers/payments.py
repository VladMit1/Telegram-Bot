import time
from telebot import types
from view.calendar_view import create_calendar
from view.pay_render import get_payments_list_markup
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controller.handlers.students import register_student_handlers 

def register_payment_handlers(bot, db, user_data, ui_refs, finance):

    # --- 1. ОТКРЫТИЕ КАЛЕНДАРЯ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay_") and 
                            not any(x in call.data for x in ["date", "history"]))
    def open_pay_calendar(call):
        chat_id = call.message.chat.id
        student_id = call.data.split("_")[1]
    
        # 1. Мгновенно меняем текст кнопки/карточки на лоадинг (через call)
        # Это дает пользователю отклик, что бот "думает"
        ui_refs['show_loading'](chat_id, "💳 <b>Загрузка календаря оплат...</b>", call=call)
    
        # 2. Получаем данные из базы
        pay_dates = db.payments.get_dates_by_student(student_id)
        markup = create_calendar(student_id, mode="pay", highlight_dates=pay_dates)
    
        # 3. Редактируем ЭТО ЖЕ сообщение, заменяя лоадинг на календарь
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"💳 <b>Оплата:</b> выберите дату\n──────────────────────────",
            reply_markup=markup,
            parse_mode="HTML"
        )
        # Теперь это сообщение — главное окно
        ui_refs['welcome_msg_id'] = call.message.message_id

    # --- 2. ВЫБОР ДАТЫ И ЗАПРОС СУММЫ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay_date_"))
    def select_date(call):
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        msg_id = call.message.message_id  # Запоминаем ID Главного Окна
        
        if user_id not in user_data:
            user_data[user_id] = {}
            
        params = call.data.split("_")
        s_id, sel_date = params[2], params[3]
        
        user_data[user_id].update({
            'step': 'waiting_pay_amount',
            'student_id': s_id,
            'pay_date': sel_date,
            'pay_instruction_id': msg_id  # <--- Теперь это ИМЕННО ID главного окна!
        })
        
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("❌ Отмена", callback_data=f"fast_view_{s_id}")
        )
        
        # Просто РЕДАКТИРУЕМ текущий календарь в экран ввода суммы
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"💰 <b>Дата: {sel_date}</b>\nВведите сумму (PLN):",
            reply_markup=markup,
            parse_mode="HTML"
        )
    # --- 3. ИСТОРИЯ ПЛАТЕЖЕЙ (СПИСОК ДЛЯ УДАЛЕНИЯ) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("history_pay_"))
    def show_payments_history(call):
        s_id = call.data.split("_")[2]
        
        # 1. Сначала ПРОВЕРЯЕМ базу, а не шлем лоадинг
        payments = db.payments.execute(
            "SELECT id, amount, payment_date FROM payments WHERE student_id = ? ORDER BY payment_date DESC LIMIT 10",
            (s_id,), fetchall=True
        )
    
        if not payments:
            # 2. Если пусто — просто вешаем уведомление сверху, экран не меняем
            bot.answer_callback_query(call.id, "❌ История платежей пуста", show_alert=True)
            return

        # 3. Если платежи есть — вот теперь показываем лоадинг и рендерим список
        ui_refs['show_loading'](call.message.chat.id, "📁 <b>Открываю историю...</b>", call=call)
        
        markup = get_payments_list_markup(s_id, payments)
        
        # Добавляем кнопку "Назад" в самый конец списка, если её нет в get_payments_list_markup
        markup.add(types.InlineKeyboardButton("🔙 Назад в профиль", callback_data=f"fast_view_{s_id}"))

        bot.edit_message_text(
            "🗑 <b>Выберите платеж для удаления:</b>\n"
            "<i>(Последние 10 операций)</i>",
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="HTML"
        )
    # --- 4. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_pay_"))
    def process_delete_payment(call):
        params = call.data.split("_")
        s_id, p_id = params[2], params[3]
        chat_id = call.message.chat.id
    
        db.payments.delete(p_id)
        bot.answer_callback_query(call.id, "✅ Платеж удален")
    
        payments = db.payments.execute(
            "SELECT id FROM payments WHERE student_id = ? LIMIT 1", (s_id,), fetchall=True
        )
        
        if payments:
            show_payments_history(call)
        else:
            from view.student_render import render_student_card
            student_data = db.students.get_by_id(s_id)
            
            if student_data:
                # Передаем finance (он должен быть доступен из аргументов родительской функции)
                render_student_card(
                    bot, 
                    chat_id, 
                    student_data, 
                    finance, 
                    is_search=True, 
                    edit_msg_id=call.message.message_id
                )
            else:
                bot.send_message(chat_id, "❌ Ошибка: ученик не найден")
# --- 5. ОБРАБОТКА ТЕКСТОВОГО ВВОДА СУММЫ ---
def handle_payment_text(bot, db, message, user_data, ui_refs, finance): # Добавь finance в аргументы
    user_id = message.from_user.id
    chat_id = message.chat.id
    state = user_data.get(user_id)
    if not state or 'student_id' not in state: return

    amount_text = message.text.strip()
    
    # Удаляем цифры, которые ввел юзер
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    if amount_text.isdigit():
        # Берем ID сообщения с инструкцией ("Введите сумму"), чтобы ПРЯМО В НЕМ открыть профиль
        instr_id = state.get('pay_instruction_id')
        
        # Сохраняем в базу
        db.payments.add(state['student_id'], int(amount_text), state['pay_date'], db.students)
        user_data[user_id]['step'] = None 

        # Получаем свежие данные ученика
        student_data = db.students.get_by_id(state['student_id'])
        
        # РЕДАКТИРУЕМ инструкцию в карточку профиля (Бесшовно)
        from view.student_render import render_student_card
        render_student_card(bot, chat_id, student_data, finance, is_search=True, edit_msg_id=instr_id)
    else:
        # Если ввел не число - просто уведомление (можно заменить на edit текущей инструкции)
        bot.send_message(chat_id, "⚠️ Введите только число!")