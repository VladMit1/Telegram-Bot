import telebot
from telebot import types
from datetime import datetime
import time
from database.db_manager import db

TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)

welcome_msg_id = None

def check_welcome_message(chat_id):
    global welcome_msg_id
    count = db.get_count()
    
    if count == 0:
        text = (
            " \n" * 5 +  # Добавит отступ сверху
            "👋 **Добро пожаловать в Tracker!**\n\n"
            "Ваш список учеников пока пуст.\n"
            "Пришлите контакт ученика, чтобы добавить его в систему."
        )
        try:
            msg = bot.send_message(chat_id, text, parse_mode="Markdown")
            welcome_msg_id = msg.message_id
        except: pass
    else:
        if welcome_msg_id:
            try:
                bot.delete_message(chat_id, welcome_msg_id)
                welcome_msg_id = None
            except: pass

# --- ОБРАБОТКА КОМАНДЫ START (Кнопка "Запуск") ---
# --- ОБРАБОТКА КОМАНДЫ START ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    # Как только нажал "Запуск", сразу удаляем это сервисное сообщение
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except: pass
    
    # Показываем приветствие только если база пуста
    check_welcome_message(message.chat.id)

# --- ОБРАБОТКА ПРИСЛАННОГО КОНТАКТА ---
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    global welcome_msg_id
    
    # 1. Сразу удаляем присланный контакт (пузырь с телефоном)
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except: pass

    # 2. УДАЛЯЕМ ПРИВЕТСТВИЕ (теперь кнопка Запуск исчезнет, так как пойдут карточки)
    if welcome_msg_id:
        try:
            bot.delete_message(message.chat.id, welcome_msg_id)
            welcome_msg_id = None
        except: pass

    c = message.contact
    name = f"{c.first_name} {c.last_name or ''}".strip()
    user_id = c.user_id 
    phone = c.phone_number
    date_now = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Ищем фото профиля (код без изменений)
    photo_file_id = None
    if user_id:
        try:
            photos = bot.get_user_profile_photos(user_id)
            if photos and photos.total_count > 0:
                photo_file_id = photos.photos[0][0].file_id
        except: pass

    # Создаем кнопки (Чат, Удалить, Статистика)
    markup = types.InlineKeyboardMarkup(row_width=2)
    chat_url = f"tg://openmessage?user_id={user_id}" if user_id else f"tel:{phone}"
    btn_chat = types.InlineKeyboardButton("💬 Чат", url=chat_url)
    btn_delete = types.InlineKeyboardButton("🗑️ Удалить", callback_data=f"del_{phone}")
    btn_stats = types.InlineKeyboardButton("📊 Статистика", callback_data=f"stats_{user_id}")
    markup.add(btn_chat, btn_delete)
    markup.add(btn_stats)

    caption = f"👤 **Ученик:** {name}\n📱 **Телефон:** `{phone}`\n📅 **Добавлен:** {date_now}"

    # 3. Отправляем карточку ученика
    sent_msg = None
    if photo_file_id:
        sent_msg = bot.send_photo(message.chat.id, photo_file_id, caption=caption, parse_mode="Markdown", reply_markup=markup)
    else:
        sent_msg = bot.send_message(message.chat.id, caption, parse_mode="Markdown", reply_markup=markup)

    # 4. Сохраняем в базу
    success = db.add_contact(name, phone, sent_msg.message_id, message.chat.id)

    if not success:
        # Если это дубликат, удаляем созданную карточку и пишем инфо
        bot.delete_message(message.chat.id, sent_msg.message_id)
        temp_msg = bot.send_message(message.chat.id, f"ℹ️ **{name}** уже есть в списке.")
        time.sleep(2)
        try: 
            bot.delete_message(message.chat.id, temp_msg.message_id)
            # Проверяем, нужно ли вернуть приветствие (если вдруг база пуста)
            check_welcome_message(message.chat.id)
        except: pass
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    if call.data.startswith('del_'):
        phone = call.data.split('_')[1]
        success = db.delete_contact_by_phone(phone)
        if success:
            try:
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.answer_callback_query(call.id, "Удалено")
                check_welcome_message(call.message.chat.id)
            except: pass
    elif call.data.startswith('stats_'):
        bot.answer_callback_query(call.id, "Статистика будет в Mini App")