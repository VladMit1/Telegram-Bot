import telebot
import json
from database.db_manager import db

API_TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(API_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    btn = telebot.types.InlineKeyboardButton(
        text="Открыть Трекер", 
        web_app=telebot.types.WebAppInfo(url="https://vladmit1.github.io/Telegram-Bot/")
    )
    markup.add(btn)
    bot.send_message(message.chat.id, "Привет! Твой список контактов:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_app_data(message):
    data = json.loads(message.web_app_data.data)
    db.add_contact(data.get('name'), data.get('time'))
    bot.send_message(message.chat.id, f"✅ {data.get('name')} добавлен в базу!")