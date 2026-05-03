import time
from telebot import types
from view.calendar_view import create_calendar
from view.pay_render import get_payments_list_markup
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from controller.handlers.students import register_student_handlers 

def register_payment_handlers(bot, db, user_data, ui_refs):

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
        if user_id not in user_data:
            user_data[user_id] = {}
            
        params = call.data.split("_")
        s_id, sel_date = params[2], params[3]
        
        user_data[user_id].update({
            'step': 'waiting_pay_amount',
            'student_id': s_id,
            'pay_date': sel_date
        })
        
        # Кнопка отмены возвращает в профиль студента
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("❌ Отмена", callback_data=f"fast_view_{s_id}")
        )
        
        # Сначала шлем новое, потом удаляем старое (календарь)
        sent_msg = bot.send_message(
            call.message.chat.id, 
            f"💰 <b>Дата: {sel_date}</b>\nВведите сумму (PLN):", 
            reply_markup=markup, 
            parse_mode="HTML"
        )
        
        user_data[user_id]['pay_instruction_id'] = sent_msg.message_id
        
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass

    # --- 3. ИСТОРИЯ ПЛАТЕЖЕЙ (СПИСОК ДЛЯ УДАЛЕНИЯ) ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("history_pay_"))
    def show_payments_history(call):
        # Здесь мы РЕДАКТИРУЕМ текущее сообщение (карточку профиля)
        ui_refs['show_loading'](call.message.chat.id, "📁 <b>Открываю историю...</b>", call=call)
        
        s_id = call.data.split("_")[2]
        payments = db.payments.execute(
            "SELECT id, amount, payment_date FROM payments WHERE student_id = ? ORDER BY payment_date DESC LIMIT 10",
            (s_id,), fetchall=True
        )
    
        if not payments:
            bot.answer_callback_query(call.id, "История пуста", show_alert=True)
            # Если пусто, возвращаем профиль назад (тоже быстро)
            call.data = f"fast_view_{s_id}"
            # Здесь вызываем функцию из students (убедись, что она доступна)
            return

        markup = get_payments_list_markup(s_id, payments)
        bot.edit_message_text(
            "🗑 <b>Выберите платеж для удаления:</b>",
            call.message.chat.id, call.message.message_id, 
            reply_markup=markup, parse_mode="HTML"
        )
    # --- 4. ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_pay_"))
    def process_delete_payment(call):
        params = call.data.split("_")
        s_id, p_id = params[2], params[3]
    
        db.payments.delete(p_id)
        bot.answer_callback_query(call.id, "✅ Платеж удален")
    
        # Проверяем, остались ли платежи, чтобы знать, что рисовать дальше
        payments = db.payments.execute(
            "SELECT id FROM payments WHERE student_id = ? LIMIT 1", (s_id,), fetchall=True
        )
        
        if payments:
            # Если еще есть платежи, обновляем список
            call.data = f"history_pay_{s_id}"
            show_payments_history(call)
        else:
            # Если пусто, возвращаемся в профиль студента
            bot.answer_callback_query(call.id, "Все платежи удалены")
            # Эмулируем вызов профиля (предполагается, что такой хендлер есть)
            call.data = f"view_stu_{s_id}"
            register_student_handlers.open_card(call)

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
        bot.send_message(chat_id, "⚠️ Введите только число!", str(chat_id))