import time
from telebot import types
from view.calendar_view import create_calendar
from view.pay_render import  get_payments_list_markup

def register_payment_handlers(bot, db, user_data, ui_refs):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay_") and not call.data.startswith("pay_date_"))
    def open_pay_calendar(call):
        student_id = call.data.split("_")[1]
        pay_dates = db.payments.get_dates_by_student(student_id)
        markup = create_calendar(student_id, mode="pay", highlight_dates=pay_dates)
        
        ui_refs['clear_screen'](call.message.chat.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "💳 <b>Финансовый календарь</b>:", 
                         reply_markup=markup, parse_mode="HTML")

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
        
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel_pay"))
        sent_msg = bot.send_message(call.message.chat.id, f"💰 <b>Дата: {sel_date}</b>\nВведите сумму:", 
                                    reply_markup=markup, parse_mode="HTML")
        user_data[user_id]['pay_instruction_id'] = sent_msg.message_id

def handle_payment_text(bot, db, message, user_data, ui_refs):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # ЗАЩИТА: Если данных нет (бот перезагрузился), выходим
    if user_id not in user_data or 'student_id' not in user_data[user_id]:
        bot.send_message(chat_id, "⚠️ Сессия истекла. Начните процесс пополнения заново.")
        return

    state = user_data[user_id]
    amount_text = message.text.strip()

    # Чистим сообщения
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    if state.get('pay_instruction_id'):
        try: bot.delete_message(chat_id, state['pay_instruction_id'])
        except: pass

    if amount_text.isdigit():
        amount = int(amount_text)
        
        # ВЫЗОВ: передаем db.students как 4-й параметр
        db.payments.add(state['student_id'], amount, state['pay_date'], db.students)
        
        temp = bot.send_message(chat_id, f"✅ Зачислено {amount} PLN!")
        user_data[user_id]['step'] = None # Сбрасываем шаг
        
        ui_refs['handle_start'](message) # Возвращаемся в меню
        
        time.sleep(3)
        try: bot.delete_message(chat_id, temp.message_id)
        except: pass
    else:
        bot.send_message(chat_id, "❌ Введите только число (целое)!")


    # controller/handlers/payments.py

# 1. Открыть список для удаления (например, по кнопке "История платежей")
    @bot.callback_query_handler(func=lambda call: call.data.startswith("history_pay_"))
    def show_payments_history(call):
        s_id = call.data.split("_")[2]
        # Получаем последние 10 платежей
        payments = db.payments.execute(
            "SELECT id, amount, payment_date FROM payments WHERE student_id     = ? ORDER BY payment_date DESC LIMIT 10",
            (s_id,), fetchall=True
        )
    
        if not payments:
            bot.answer_callback_query(call.id, "История платежей пуста")
            return

        markup = get_payments_list_markup(s_id, payments)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🗑 <b>Выберите платеж для удаления:</b>\n<i>(Баланс пересчитается автоматически)</i>",
            reply_markup=markup,
            parse_mode="HTML"
        )

# 2. Само удаление
    @bot.callback_query_handler(func=lambda call: call.data.startswith("del_pay_"))
    def process_delete_payment(call):
        params = call.data.split("_")
        s_id, p_id = params[2], params[3]
    
        # Удаляем из базы
        db.payments.delete(p_id)
    
        bot.answer_callback_query(call.id, "✅ Платеж удален")
    
        # Обновляем список или возвращаемся в профиль
        # Здесь можно вызвать ту же функцию show_payments_history, чтобы обновить список
        call.data = f"history_pay_{s_id}"
        show_payments_history(call)