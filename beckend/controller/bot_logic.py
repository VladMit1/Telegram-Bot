import telebot
from database.db_manager import db

TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    c = message.contact
    name = f"{c.first_name} {c.last_name or ''}".strip()
    user_id = c.user_id 

    # 1. Удаляем присланную карточку контакта сразу
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except: pass

    # 2. Получаем фото профиля
    photo_file_id = None
    if user_id:
        try:
            photos = bot.get_user_profile_photos(user_id)
            if photos and photos.total_count > 0:
                photo_file_id = photos.photos[0][0].file_id
        except: pass

    # 3. Отправляем подтверждение (сообщение от БОТА)
    caption = f"✅ Ученик **{name}** добавлен в список!"
    if photo_file_id:
        sent_msg = bot.send_photo(message.chat.id, photo_file_id, caption=caption, parse_mode="Markdown")
    else:
        sent_msg = bot.send_message(message.chat.id, caption, parse_mode="Markdown")

    # 4. Сохраняем ID сообщения БОТА, чтобы потом его удалить через API
    success = db.add_contact(name, c.phone_number, sent_msg.message_id, message.chat.id)

    if not success:
        # Если такой контакт уже есть, удаляем лишнее сообщение бота
        bot.delete_message(message.chat.id, sent_msg.message_id)
        bot.send_message(message.chat.id, f"ℹ️ {name} уже был в списке.")