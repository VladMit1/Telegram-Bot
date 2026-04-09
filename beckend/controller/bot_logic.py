import telebot
from telebot import types
import time
from database.db_manager import db

TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)

welcome_msg_id = None
search_results_ids = []

def render_student_card(chat_id, student_data, is_search=False):
    name = student_data[1]
    phone = student_data[2]
    date_added = student_data[3] if len(student_data) > 3 else "Сегодня"
    photo_id = student_data[4] if len(student_data) > 4 else None
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💬 Написать", url=f"https://t.me/{phone}"),
        types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_{phone}")
    )
    markup.add(types.InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{phone}"))
    
    # Если в режиме поиска, добавляем кнопку возврата
    if is_search:
        markup.add(types.InlineKeyboardButton("🔙 Назад к списку", callback_data="show_all"))

    caption = f"👤 <b>Ученик:</b> {name}\n📱 <b>Телефон:</b> <code>{phone}</code>\n📅 <b>Добавлен:</b> {date_added}"
    
    try:
        if photo_id:
            msg = bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="HTML", reply_markup=markup)
        else:
            msg = bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)
        return msg.message_id
    except:
        msg = bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup)
        return msg.message_id

def check_welcome_message(chat_id):
    global welcome_msg_id
    count = db.get_count()
    if count == 0:
        if welcome_msg_id is None:
            try:
                msg = bot.send_message(chat_id, "👋 <b>Список пуст.</b>\nПришлите контакт!", parse_mode="HTML")
                welcome_msg_id = msg.message_id
            except: pass
    else:
        if welcome_msg_id:
            try: bot.delete_message(chat_id, welcome_msg_id)
            except: pass
            welcome_msg_id = None

@bot.message_handler(commands=['start'])
def handle_start(message):
    global search_results_ids, welcome_msg_id
    try: bot.delete_message(message.chat.id, message.message_id)
    except: pass
    
    for m_id in search_results_ids:
        try: bot.delete_message(message.chat.id, m_id)
        except: pass
    search_results_ids.clear()
    
    contacts = db.get_all()
    if not contacts:
        welcome_msg_id = None
        check_welcome_message(message.chat.id)
    else:
        if welcome_msg_id:
            try: bot.delete_message(message.chat.id, welcome_msg_id)
            except: pass
            welcome_msg_id = None
        for c in contacts:
            search_results_ids.append(render_student_card(message.chat.id, c))

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    global welcome_msg_id
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
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
    
    if db.add_contact(name, c.phone_number, photo_id, chat_id):
        if welcome_msg_id:
            try: bot.delete_message(chat_id, welcome_msg_id)
            except: pass
            welcome_msg_id = None
            
        new_data = (None, name, c.phone_number, "Сегодня", photo_id)
        msg_id = render_student_card(chat_id, new_data)
        search_results_ids.append(msg_id)
    else:
        temp = bot.send_message(chat_id, f"ℹ️ {name} уже в списке.")
        time.sleep(3)
        try: bot.delete_message(chat_id, temp.message_id)
        except: pass

# --- ВОТ ОН, ВЕРНУВШИЙСЯ ПОИСК ---
@bot.message_handler(content_types=['text'])
def handle_search_text(message):
    global search_results_ids
    query = message.text.strip()
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass

    results = db.search_contacts(query)
    
    # Очищаем экран перед показом результатов
    for msg_id in search_results_ids:
        try: bot.delete_message(chat_id, msg_id)
        except: pass
    search_results_ids.clear()

    if not results:
        temp = bot.send_message(chat_id, f"🔍 По запросу «{query}» ничего не найдено.")
        time.sleep(2)
        try: bot.delete_message(chat_id, temp.message_id)
        except: pass
        handle_start(message)
        return

    for r in results:
        msg_id = render_student_card(chat_id, r, is_search=True)
        search_results_ids.append(msg_id)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global welcome_msg_id
    chat_id = call.message.chat.id
    
    if call.data == "show_all":
        bot.answer_callback_query(call.id)
        handle_start(call.message)

    elif call.data.startswith('del_'):
        phone = call.data.split('_')[1]
        try:
            bot.delete_message(chat_id, call.message.message_id)
            if call.message.message_id in search_results_ids:
                search_results_ids.remove(call.message.message_id)
        except: pass
        
        db.delete_contact_by_phone(phone)
        bot.answer_callback_query(call.id, "Удалено")
        
        if db.get_count() == 0:
            welcome_msg_id = None
            check_welcome_message(chat_id)

    elif call.data.startswith('stats_'):
        bot.answer_callback_query(call.id, "Статистика в Mini App")