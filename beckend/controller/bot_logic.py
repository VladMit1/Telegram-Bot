import os
import telebot
from dotenv import load_dotenv
from telebot import types
import time
from database.db_manager import db 

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    print("❌ Ошибка: BOT_TOKEN не найден в .env файле")
    exit(1)
bot = telebot.TeleBot(TOKEN)

# Глобальные переменные
welcome_msg_id = None
search_results_ids = []
user_data = {} 

def get_main_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data="add_student"))
    return markup

def render_student_card(chat_id, student_data, is_search=False, show_add_button=False):
    """Отрисовка карточки ученика с умной кнопкой связи"""
    student_id, name, phone = student_data[0], student_data[1], student_data[2]
    date_added = student_data[3]
    photo_id = student_data[4]
    
    web_app_url = f"https://vladmit1.github.io/Telegram-Bot/?studentId={student_id}"
    markup = types.InlineKeyboardMarkup(row_width=2)

    # ЕДИНАЯ ЛОГИКА КНОПКИ "НАПИСАТЬ"
    chat_url = None
    
    # Пытаемся вытащить никнейм из любого поля
    search_str = f"{name} {phone}"
    if "@" in search_str:
        for word in search_str.split():
            if word.startswith("@"):
                chat_url = f"https://t.me/{word.replace('@', '')}"
                break
    
    # Если ника нет, используем номер (чистим от мусора)
    if not chat_url and phone and not str(phone).startswith("id_") and phone != "no_phone":
        clean_phone = "".join(filter(str.isdigit, str(phone)))
        # Для международных номеров t.me/+7999... работает лучше всего
        chat_url = f"https://t.me/+{clean_phone}"

    if chat_url:
        markup.add(types.InlineKeyboardButton("💬 Написать", url=chat_url))
    
    # Остальные кнопки
    markup.add(
        types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_{student_id}"),
        types.InlineKeyboardButton("📊 Статистика", web_app=types.WebAppInfo(url=web_app_url))
    )
    
    if is_search:
        markup.add(types.InlineKeyboardButton("🔙 Назад к списку", callback_data="show_all"))
    if show_add_button:
        markup.add(types.InlineKeyboardButton("➕ Добавить ученика", callback_data="add_student"))

    display_phone = phone if phone and not str(phone).startswith("id_") else "Не указан"
    caption = (f"👤 <b>Ученик:</b> {name}\n"
               f"📱 <b>Телефон:</b> <code>{display_phone}</code>\n"
               f"📅 <b>Добавлен:</b> {date_added}")
    
    try:
        if photo_id:
            return bot.send_photo(chat_id, photo_id, caption=caption, parse_mode="HTML", reply_markup=markup).message_id
        else:
            return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup).message_id
    except:
        return bot.send_message(chat_id, caption, parse_mode="HTML", reply_markup=markup).message_id
@bot.message_handler(commands=['start'])
def handle_start(message):
    global search_results_ids, welcome_msg_id
    chat_id = message.chat.id
    
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    
    if welcome_msg_id:
        try: bot.delete_message(chat_id, welcome_msg_id)
        except: pass
        welcome_msg_id = None

    for m_id in search_results_ids:
        try: bot.delete_message(chat_id, m_id)
        except: pass
    search_results_ids.clear()
    
    contacts = db.get_all()
    
    if not contacts:
        msg = bot.send_message(chat_id, "👋 <b>Список пуст.</b>", 
                               parse_mode="HTML", reply_markup=get_main_markup())
        welcome_msg_id = msg.message_id
    else:
        for i, c in enumerate(contacts):
            is_last = (i == len(contacts) - 1)
            m_id = render_student_card(chat_id, c, show_add_button=is_last)
            search_results_ids.append(m_id)

@bot.callback_query_handler(func=lambda call: call.data == "add_student")
def start_manual_add(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    user_data[user_id] = {'step': 'waiting_name'} 
    msg = bot.send_message(call.message.chat.id, "📝 <b>Введите данные:</b> (@username Имя)")
    user_data[user_id]['last_msg'] = msg.message_id
    bot.register_next_step_handler(msg, process_input)

def process_input(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    if user_id in user_data and 'last_msg' in user_data[user_id]:
        try: bot.delete_message(chat_id, user_data[user_id]['last_msg'])
        except: pass

    if not message.text or message.text.startswith('/'):
        if message.text == '/start': handle_start(message)
        return

    user_data[user_id]['temp_name'] = message.text
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Утвердить", callback_data="confirm_save"),
        types.InlineKeyboardButton("🔄 Исправить", callback_data="add_student")
    )
    msg = bot.send_message(chat_id, f"🧐 <b>Записать так?</b>\n<code>{message.text}</code>", 
                           reply_markup=markup, parse_mode="HTML")
    user_data[user_id]['last_msg'] = msg.message_id

@bot.callback_query_handler(func=lambda call: call.data == "confirm_save")
def confirm_save(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    if user_id not in user_data: return

    final_text = user_data[user_id]['temp_name']
    fake_phone = f"id_{int(time.time())}" 
    
    if db.add_contact(final_text, fake_phone, None, chat_id):
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        del user_data[user_id]
        bot.answer_callback_query(call.id, "✅ Добавлено")
        handle_start(call.message)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    try: bot.delete_message(chat_id, message.message_id)
    except: pass
    c = message.contact
    name = f"{c.first_name} {c.last_name or ''}".strip()
    if db.add_contact(name, c.phone_number, None, chat_id):
        handle_start(message)

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    if call.data == "show_all":
        handle_start(call.message)
    elif call.data.startswith('del_'):
        s_id = call.data.split('_')[1]
        db.delete_contact(s_id) 
        bot.answer_callback_query(call.id, "🗑️ Удалено")
        handle_start(call.message)

@bot.message_handler(content_types=['text'])
def handle_search_text(message):
    global search_results_ids
    if message.from_user.id in user_data: return
    query = message.text.strip()
    results = db.search_contacts(query)
    if results:
        for m_id in search_results_ids:
            try: bot.delete_message(message.chat.id, m_id)
            except: pass
        search_results_ids.clear()
        for r in results:
            search_results_ids.append(render_student_card(message.chat.id, r, is_search=True))

if __name__ == '__main__':
    bot.polling(none_stop=True)