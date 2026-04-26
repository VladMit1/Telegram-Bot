
from datetime import datetime
from telebot import types
from database.db_manager import db # Импортируем базу
from .calendar_view import create_calendar



def render_pay_pad(bot, chat_id, student_data, selected_date=None):
   student_id = student_data[0]
   name = student_data[1]
   
   # Если дата не передана, берем сегодня
   if not selected_date:
      selected_date = datetime.now().strftime("%Y-%m-%d")
   
   # 1. Получаем историю платежей для отображения монеток
   # Тебе нужно будет добавить метод get_payments_dates в DBManager
   payment_dates = db.get_payment_dates(student_id) 
   
   # 2. Создаем календарь
   # Мы используем твой create_calendar, но добавим в него логику "монеток"
   markup = create_calendar(student_id, mode="pay", highlight_dates=payment_dates)
   
   # 3. Добавляем кнопку подтверждения даты или отмены
   markup.add(
      types.InlineKeyboardButton(f"✅ Выбрать {selected_date}", callback_data=f"set_pay_date_{student_id}_{selected_date}")
   )
   markup.add(types.InlineKeyboardButton("❌ Отмена", callback_data=f"back_to_card_{student_id}"))

   caption = (f"💳 <b>Пополнение баланса</b>\n"
               f"👤 <b>Ученик:</b> {name}\n"
               f"📅 <b>Дата платежа:</b> {selected_date}\n\n"
               f"Выберите дату на календаре (💰 — дни оплат) и нажмите кнопку ниже, чтобы ввести сумму.")

   return bot.send_message(chat_id, caption, reply_markup=markup, parse_mode="HTML").message_id