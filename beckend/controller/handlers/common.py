import os
import sys
from datetime import datetime  # Поправил для работы datetime.now()
from telebot import types

# Твои пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорты вьюх и хелперов
from view.student_render import render_student_list, get_main_markup
from view.calendar_view import create_calendar, create_months_select, create_years_select
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
            # Если пусто — трансформируем в "Пусто"
            bot.edit_message_text(
                text="👋 <b>Нет активных учеников</b>", 
                chat_id=chat_id, 
                message_id=call.message.message_id, 
                reply_markup=get_main_markup(), 
                parse_mode="HTML"
            )
        else:
            # ТРАНСФОРМАЦИЯ: Превращаем форму ввода обратно в список учеников
            render_student_list(
                bot, 
                chat_id, 
                contacts, 
                finance, 
                edit_msg_id=call.message.message_id # Передаем ID сообщения для редактирования
            )
    @bot.callback_query_handler(func=lambda call: call.data.startswith("cal_nav_"))
    @safe_handler(bot)
    def handle_calendar_navigation(call):
        params = call.data.split("_")
        student_id = params[2] 
        mode = params[3]
        year, month = int(params[4]), int(params[5])

        highlight_dates = []
        if student_id == "all":
            text = "📅 <b>Общий календарь загрузки:</b>"
        else:
            text = "💳 <b>Финансовый календарь:</b>" if mode == "pay" else "📅 <b>Расписание занятий:</b>"

        if mode == "pay" and student_id != "all":
            highlight_dates = db.payments.get_dates_by_student(student_id)

        markup = create_calendar(student_id, year, month, mode, highlight_dates, db)

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
            if not student:
                bot.answer_callback_query(call.id, "Ученик не найден", show_alert=True)
                return

            # Готовый вариант возврата
            back_callback = f"fast_view_{student_id}"

            # 1. Получаем доступные года и выбранный год
            student_years = finance.get_student_years(student_id)
            if not student_years:
                student_years = [datetime.now().year]

            if len(data_parts) > 3 and data_parts[3].isdigit():
                selected_year = int(data_parts[3])
            else:
                selected_year = student_years[-1]

            # 2. Данные за выбранный год
            year_data = finance.get_student_yearly_report(student_id, selected_year) if hasattr(finance, 'get_student_yearly_report') else {'lessons_count': 0, 'spent': 0, 'paid': 0}
            
            # 3. Данные ЗА ВСЁ ВРЕМЯ (глобальные)
            global_student_data = finance.get_student_global_report(student_id) if hasattr(finance, 'get_student_global_report') else {
                'total_lessons': year_data.get('lessons_count', 0),
                'total_spent': year_data.get('spent', 0),
                'total_paid': year_data.get('paid', 0),
                'balance': finance.get_actual_balance(student_id)
            }

            total_balance = global_student_data.get('balance', 0)

            # 4. Форматирование статуса баланса
            if total_balance > 0:
                balance_status = f"🟢 <b>Аванс ученика:</b> <code>{total_balance:,} PLN</code>".replace(",", " ")
            elif total_balance < 0:
                balance_status = f"🔴 <b>Долг ученика:</b> <code>{abs(total_balance):,} PLN</code>".replace(",", " ")
            else:
                balance_status = "⚪️ <b>Баланс:</b> <code>0 PLN</code>"

            # 5. Разделители тысяч для сумм (пробелы)
            y_spent = f"{year_data.get('spent', 0):,}".replace(",", " ")
            y_paid = f"{year_data.get('paid', 0):,}".replace(",", " ")
            g_spent = f"{global_student_data.get('total_spent', 0):,}".replace(",", " ")
            g_paid = f"{global_student_data.get('total_paid', 0):,}".replace(",", " ")

            # 6. Сборка карточки
            text = (
                f"👤 <b>ФИНАНСЫ УЧЕНИКА: {student['name']} (ID: {student_id})</b>\n"
                f"──────────────────────────\n"
                f"📅 <b>Статистика за год:</b>\n\n"
                f"▫️ <b>{selected_year} год:</b>\n"
                f"   • Проведено уроков: {year_data.get('lessons_count', 0)} (<code>{y_spent} PLN</code>)\n"
                f"   • Оплачено: <code>{y_paid} PLN</code>\n"
                f"──────────────────────────\n"
                f"🌐 <b>ИТОГО ЗА ВСЁ ВРЕМЯ:</b>\n"
                f"📚 Всего уроков: {global_student_data.get('total_lessons', 0)} (<code>{g_spent} PLN</code>)\n"
                f"💰 Всего оплачено: <code>{g_paid} PLN</code>\n"
                f"{balance_status}"
            )

            markup = types.InlineKeyboardMarkup()

            # Кнопки выбора годов
            if len(student_years) > 1:
                year_buttons = []
                for yr in student_years:
                    btn_text = f"• {yr} •" if yr == selected_year else str(yr)
                    # Используем валидный callback для выбранной кнопки (чтобы при клике на нее не вылетала ошибка)
                    cb_data = f"report_student_{student_id}_{yr}" if yr != selected_year else f"ignore_year_{yr}"
                    year_buttons.append(types.InlineKeyboardButton(btn_text, callback_data=cb_data))
                markup.row(*year_buttons)

            # Кнопка возврата с использованием вашего back_callback
            markup.add(types.InlineKeyboardButton("🔙 Назад в профиль", callback_data=back_callback))
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
    
    # --- 1. РЕНДЕР СЕТКИ МЕСЯЦЕВ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_months_"))
    def handle_open_months(call):
        # Разбираем callback: open_months_{student_id}_{mode}_{year}
        parts = call.data.split("_")
        s_id, mode, year = parts[2], parts[3], parts[4]
        
        # Импортируем функцию из файла, где лежит наш календарь
        
        markup = create_months_select(s_id, mode, year)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🗓 <b>Выберите месяц:</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )

    # --- 2. РЕНДЕР СЕТКИ ГОДОВ ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("open_years_"))
    def handle_open_years(call):
        # Разбираем callback: open_years_{student_id}_{mode}_{current_year}
        parts = call.data.split("_")
        s_id, mode, year = parts[2], parts[3], parts[4]
        
        markup = create_years_select(s_id, mode, year)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="📅 <b>Выберите год:</b>",
            reply_markup=markup,
            parse_mode="HTML"
        )
    @bot.callback_query_handler(func=lambda call: call.data.startswith("ignore_year_"))
    def ignore_year_callback(call):
        bot.answer_callback_query(call.id, text="Этот год уже выбран")
    return handle_start