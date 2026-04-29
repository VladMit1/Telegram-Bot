import time
from telebot import types
from view.calendar_view import create_calendar

def register_payment_handlers(bot, db, user_data, ui_refs):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay_") and not call.data.startswith("pay_date_"))
    def open_pay_calendar(call):
        student_id = call.data.split("_")[1]
        pay_dates = db.get_payment_dates(student_id)
        markup = create_calendar(student_id, mode="pay", highlight_dates=pay_dates)
        
        ui_refs['clear_screen'](call.message.chat.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        bot.send_message(call.message.chat.id, "💳 <b>Финансовый календарь</b>:", 
                         reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("pay_date_"))
    def select_date(call):
        user_id = call.from_user.id
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
    state = user_data[user_id]
    amount_text = message.text.strip()

    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    if state.get('pay_instruction_id'):
        try: bot.delete_message(chat_id, state['pay_instruction_id'])
        except: pass

    if amount_text.isdigit():
        db.add_payment(state['student_id'], int(amount_text), state['pay_date'])
        temp = bot.send_message(chat_id, f"✅ Зачислено {amount_text}!")
        user_data[user_id]['step'] = None
        ui_refs['handle_start'](message)
        time.sleep(3)
        try: bot.delete_message(chat_id, temp.message_id)
        except: pass
    else:
        err = bot.send_message(chat_id, "❌ Введите только число!")
        time.sleep(2)
        try: bot.delete_message(chat_id, err.message_id)
        except: pass