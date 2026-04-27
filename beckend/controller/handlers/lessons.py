from telebot import types
from view.calendar_view import create_calendar

def register_lesson_handlers(bot, db, ui_refs):

    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_calendar_"))
    def lessons_cal(call):
        student_id = call.data.split("_")[2]
        ui_refs['clear_screen'](call.message.chat.id)
        try: bot.delete_message(call.message.chat.id, call.message.message_id)
        except: pass
        markup = create_calendar(student_id)
        bot.send_message(call.message.chat.id, "📅 <b>Расписание:</b>", 
                         reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_day_"))
    def select_lesson_day(call):
        d = call.data.split("_")
        s_id, sel_date = d[2], f"{d[3]}-{d[4].zfill(2)}-{d[5].zfill(2)}"
        booked = db.get_booked_times_with_names(sel_date)
        
        markup = types.InlineKeyboardMarkup(row_width=4)
        slots = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00", "16:00"]
        btns = [types.InlineKeyboardButton(f"🚫 {t}" if t in booked else t, 
                callback_data="ignore" if t in booked else f"stme_{s_id}_{sel_date}_{t}") for t in slots]
        markup.add(*btns).add(types.InlineKeyboardButton("🔙 Назад", callback_data=f"open_calendar_{s_id}"))
        bot.edit_message_text(f"📅 <b>{sel_date}</b>", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("stme_"))
    def save_lesson(call):
        d = call.data.split("_")
        db.add_lesson(d[1], d[2], d[3])
        bot.answer_callback_query(call.id, "✅ Записано")
        ui_refs['handle_start'](call.message)