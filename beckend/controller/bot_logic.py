import telebot
import json
from database.db_manager import db

TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    web_app = telebot.types.WebAppInfo(url="https://vladmit1.github.io/Telegram-Bot/")
    btn = telebot.types.InlineKeyboardButton("Открыть Трекер 📱", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "Пришли контакт через 📎 (скрепку), и он появится в списке!", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    c = message.contact
    name = f"{c.first_name} {c.last_name or ''}".strip()
    # Сохраняем в базу
    db.add_contact(name, "12:00", c.phone_number)
    bot.send_message(message.chat.id, f"✅ {name} добавлен!")

bot.polling(none_stop=True)