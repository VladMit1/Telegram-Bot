import telebot
from telebot import types
import time
from database.db_manager import db

TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)

welcome_msg_id = None
search_results_ids = []

def render_student_card(chat_id, student_data, is_search=False):
    """student_data: (id, name, phone, date, photo_id)"""
    name = student_data[1]
    phone = student_data[2]
    date_added = student_data[3] if len(student_data) > 3 else "Сегодня"
    photo_id = student_data[4] if len(student_data) > 4 else None
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_chat = types.InlineKeyboardButton("💬 Написать", url=f"https://t.me/{phone}")
    btn_delete = types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_{phone}")
    btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{phone}")
    markup.add(btn_chat, btn_delete, btn_stats)
    
    if is_search:
        markup.add(types.InlineKeyboardButton("🔙 Назад к списку", callback_data="show_all"))

    # ИСПОЛЬЗУЕМ HTML ТЕГИ ВМЕСТО ЗВЕЗДОЧЕК
    caption = (
        f"👤 <b>Ученик:</b> {name}\n"
        f"📱 <b>Телефон:</b> <code>{phone}</code>\n"
        f"📅 <b>Добавлен:</b> {date_added}"
    )
    
    try:
        if photo_id:
            # МЕНЯЕМ Markdown на HTML
            msg = bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="HTML", reply_markup=markup)
        else:
            msg = bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)
        return msg.message_id
    except Exception as e:
        print(f"Ошибка при отправке: {e}")
        # Если даже HTML упал (например, в имени есть знак <), шлем чистый текст
        msg = bot.send_message(chat_id, f"Ученик: {name}\nТелефон: {phone}", reply_markup=markup)
        return msg.message_id
def show_full_list(chat_id):
    global search_results_ids, welcome_msg_id
    # Сначала пытаемся удалить всё старое
    for msg_id in search_results_ids:
        try: bot.delete_message(chat_id, msg_id)
        except: pass
    search_results_ids.clear()

    # Проверяем базу
    contacts = db.get_all()
    if not contacts:
        # Если пусто - вызываем проверку приветствия
        check_welcome_message(chat_id)
    else:
        # Если есть данные - удаляем приветствие и рисуем список
        if welcome_msg_id:
            try: bot.delete_message(chat_id, welcome_msg_id)
            except: pass
            welcome_msg_id = None
        
        for c in contacts:
            msg_id = render_student_card(chat_id, c)
            search_results_ids.append(msg_id)

def check_welcome_message(chat_id):
    global welcome_msg_id
    # Если в базе 0 и сообщения еще нет на экране - отправляем
    if db.get_count() == 0:
        if welcome_msg_id is None:
            try:
                text = "👋 <b>Список пуст.</b>\nПришлите контакт ученика, чтобы начать работу."
                msg = bot.send_message(chat_id, text, parse_mode="HTML")
                welcome_msg_id = msg.message_id
            except: pass
    else:
        # Если база не пуста, а приветствие висит - удаляем его
        if welcome_msg_id:
            try: bot.delete_message(chat_id, welcome_msg_id)
            except: pass
            welcome_msg_id = None

@bot.message_handler(commands=['start'])
def handle_start(message):
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    show_full_list(message.chat.id)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    global welcome_msg_id
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    
    c = message.contact
    photo_id = None
    if c.user_id:
        try:
            photos = bot.get_user_profile_photos(c.user_id)
            if photos and photos.total_count > 0:
                photo_id = photos.photos[0][0].file_id
        except: pass

    name = f"{c.first_name} {c.last_name or ''}".strip()
    
    # 1. Пробуем сохранить в базу
    if db.add_contact(name, c.phone_number, photo_id, message.chat.id):
        # 2. Если это первый контакт, удаляем сообщение "Список пуст"
        if welcome_msg_id:
            try: bot.delete_message(message.chat.id, welcome_msg_id); welcome_msg_id = None
            except: pass
            
        # 3. Плавное добавление: рисуем ОДНУ карточку в конце
        # Данные берем текущие, дату ставим "Сегодня"
        new_student = (None, name, c.phone_number, "Сегодня", photo_id)
        msg_id = render_student_card(message.chat.id, new_student)
        
        # Запоминаем ID, чтобы потом его можно было очистить поиском
        search_results_ids.append(msg_id)
    else:
        temp = bot.send_message(message.chat.id, f"ℹ️ {name} уже есть в списке.")
        time.sleep(2)
        try: bot.delete_message(message.chat.id, temp.message_id)
        except: pass

@bot.message_handler(content_types=['text'])
def handle_search_text(message):
    global search_results_ids
    query = message.text.strip()
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass

    results = db.search_contacts(query)
    
    for msg_id in search_results_ids:
        try: bot.delete_message(message.chat.id, msg_id)
        except: pass
    search_results_ids.clear()

    if not results:
        temp = bot.send_message(message.chat.id, f"🔍 «{query}» не найден.")
        time.sleep(2)
        try: bot.delete_message(message.chat.id, temp.message_id)
        except: pass
        show_full_list(message.chat.id)
        return

    for r in results:
        msg_id = render_student_card(message.chat.id, r, is_search=True)
        search_results_ids.append(msg_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global welcome_msg_id
    
    if call.data == "show_all":
        bot.answer_callback_query(call.id)
        show_full_list(call.message.chat.id)
        
    elif call.data.startswith('del_'):
        phone = call.data.split('_')[1]
        chat_id = call.message.chat.id
        
        # 1. Удаляем карточку из чата
        try:
            bot.delete_message(chat_id, call.message.message_id)
            if call.message.message_id in search_results_ids:
                search_results_ids.remove(call.message.message_id)
        except: pass
        
        # 2. Удаляем из базы
        db.delete_contact_by_phone(phone)
        bot.answer_callback_query(call.id, "Контакт удален")
        
        # 3. Самый важный момент: если база опустела
        if db.get_count() == 0:
            # Обнуляем всё и форсированно шлем приветствие
            search_results_ids.clear()
            welcome_msg_id = None # Сбрасываем, чтобы check_welcome_message сработал
            check_welcome_message(chat_id)
            
    elif call.data.startswith('stats_'):
        bot.answer_callback_query(call.id, "Статистика в Mini App")