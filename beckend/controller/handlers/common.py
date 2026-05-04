import os
import sys
from datetime import datetime  # Поправил для работы datetime.now()
from telebot import types

# Твои пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорты вьюх и хелперов
from view.student_render import render_student_list, get_main_markup
from view.calendar_view import create_calendar
from helper.error_handler import safe_handler
from helper.ui_utils import save_last_msg, delete_last_msg # Добавил, если они используются

def register_common_handlers(bot, db, finance, user_data, ui_refs):
    
    @bot.message_handler(commands=['start'])
    @safe_handler(bot)
    def handle_start(message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        user_data[user_id] = {'step': None}
        
        try: 
            bot.delete_message(chat_id, message.message_id)
        except: 
            pass
        
        # Полная очистка экрана
        ui_refs['clear_screen'](chat_id)
        
        contacts = db.students.get_active_students()
        
        if not contacts:
            msg = bot.send_message(
                chat_id, 
                "👋 <b>Нет активных учеников</b>\n\n<i>Добавьте первого или проверьте архив:</i>", 
                parse_mode="HTML", 
                reply_markup=get_main_markup()
            )
            ui_refs['welcome_msg_id'] = msg.message_id
        else:
            m_id = render_student_list(bot, chat_id, contacts, finance)
            ui_refs['welcome_msg_id'] = m_id

    @bot.callback_query_handler(func=lambda call: call.data in ["show_all", "main_menu", "cancel_add", "cancel_pay"])
    @safe_handler(bot)
    def handle_back(call):
        bot.answer_callback_query(call.id)
        chat_id = call.message.chat.id
        user_id = call.from_user.id
    
        if user_id in user_data:
            user_data[user_id]['step'] = None
    
        contacts = db.students.get_active_students()
    
        if not contacts:
            try:
                bot.edit_message_text(
                    text="👋 <b>Нет активных учеников</b>", 
                    chat_id=chat_id, 
                    message_id=call.message.message_id, 
                    reply_markup=get_main_markup(), 
                    parse_mode="HTML"
                )
            except:
                msg = bot.send_message(chat_id, "👋 <b>База пуста:</b>", reply_markup=get_main_markup(), parse_mode="HTML")
                ui_refs['welcome_msg_id'] = msg.message_id
        else:
            render_student_list(
                bot, 
                chat_id, 
                contacts, 
                finance, 
                edit_msg_id=call.message.message_id
            )
            ui_refs['search_results_ids'] = []

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_nav_"))
    @safe_handler(bot)
    def handle_calendar_navigation(call):
        params = call.data.split("_")
        student_id = params[2] 
        mode = params[3]
        year, month = int(params[4]), int(params[5])

        highlight_dates = None
        if student_id == "all":
            text = "📅 <b>Общий календарь загрузки:</b>"
        else:
            text = "💳 <b>Финансовый календарь:</b>" if mode == "pay" else "📅 <b>Расписание занятий:</b>"

        if mode == "pay" and student_id != "all":
            highlight_dates = db.payments.get_dates_by_student(student_id)

        markup = create_calendar(student_id, year, month, mode, highlight_dates)

        try:
            bot.edit_message_text(text, call.message.chat.id, call.message.message_id, 
                                  reply_markup=markup, parse_mode="HTML")
        except:
            pass
    
    @bot.callback_query_handler(func=lambda call: call.data == "show_archive")
    @safe_handler(bot)
    def handle_show_archive(call):
        # 1. Получаем список
        archived = db.students.get_archived_students()
    
        if not archived:
            # Показываем всплывающее окно, сообщение при этом НЕ трогаем
            bot.answer_callback_query(call.id, "📭 Архив пока пуст", show_alert=True)
            return

        # 2. Если не пуст — редактируем текущее сообщение под архив
        bot.answer_callback_query(call.id) # Убираем "часики" с кнопки
        render_student_list(
            bot, 
            call.message.chat.id, 
            archived, 
            finance, 
            edit_msg_id=call.message.message_id, 
            is_archive=True
        )

    @bot.callback_query_handler(func=lambda call: call.data == "finance_view")
    @safe_handler(bot)
    def show_finance_report(call):
        data = finance.get_global_report()

        report_text = (
            "📊 <b>ФИНАНСОВЫЙ ОТЧЕТ (ВСЕ)</b>\n"
            "──────────────────────────\n"
            f"💰 <b>Всего зашло:</b> <code>{data['total_income']} PLN</code>\n"
            f"📖 <b>Отработано:</b> <code>{data['total_spent']} PLN</code>\n"
            f"⏳ <b>В системе:</b> <code>{data['balance_in_system']} PLN</code>\n"
            f"🔴 <b>Общий долг:</b> <code>{data['total_debt']} PLN</code>\n"
            "──────────────────────────\n"
            "<i>Расчет на основе транзакций</i>"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data="main_menu"))

        bot.edit_message_text(report_text, call.message.chat.id, call.message.message_id, 
                              reply_markup=markup, parse_mode="HTML")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
    @safe_handler(bot)
    def handle_finance_reports(call):
        chat_id = call.message.chat.id
        data_parts = call.data.split("_")
        student_id = data_parts[1] if len(data_parts) > 1 and data_parts[1] else None

        if student_id:
            # --- ОТЧЕТ ПО УЧЕНИКУ ---
            student = db.students.get_by_id(student_id)
            balance = finance.get_actual_balance(student_id)
            history = finance.get_student_history_by_months(student_id)
        
            history_text = ""
            for row in history:
                month, paid, spent = row
                # Формируем строку: "05.2024: 📥500 / 📤450"
                history_text += f"📅 <b>{month}:</b> 📥<code>{paid}</code> / 📤<code>{spent}</code>\n"

            text = (
                f"👤 <b>Финансы: {student['name']}</b>\n"
                f"──────────────────────────\n"
                f"💰 <b>Текущий баланс:</b> <code>{balance} PLN</code>\n\n"
                f"📊 <b>История (Месяц: Оплата/Уроки):</b>\n"
                f"{history_text if history_text else '<i>Данных пока нет</i>'}\n"
                f"──────────────────────────"
            )
            back_callback = f"fast_view_{student_id}"
        else:
            # --- ОБЩИЙ ОТЧЕТ (ПО ГОДАМ) ---
            data = finance.get_global_report()
            yearly = finance.get_total_yearly_stats()

            yearly_text = ""
            for year, sum_val in yearly:
                yearly_text += f"📅 <b>{year} год:</b> <code>{sum_val} PLN</code> (всего касса)\n"

            text = (
                "📊 <b>ГЛОБАЛЬНЫЙ ОТЧЕТ ПО ШКОЛЕ</b>\n"
                "──────────────────────────\n"
                f"{yearly_text}\n"
                f"──────────────────────────\n"
                f"📖 <b>Отработано уроков:</b> <code>{data['total_spent']} PLN</code>\n"
                f"⏳ <b>Авансы в системе:</b> <code>{data['balance_in_system']} PLN</code>\n"
                f"🔴 <b>Общий долг нам:</b> <code>{data['total_debt']} PLN</code>"
            )
            back_callback = "main_menu"

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Назад", callback_data=back_callback))
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
    
    

    return handle_start