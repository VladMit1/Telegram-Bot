import telebot
import json
from database.db_manager import db

TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    # Ссылка на твой GitHub Pages
    web_app = telebot.types.WebAppInfo(url="https://vladmit1.github.io/Telegram-Bot/")
    btn = telebot.types.InlineKeyboardButton("Открыть Трекер", web_app=web_app)
    markup.add(btn)
    bot.send_message(message.chat.id, "Привет! Твой список контактов:", reply_markup=markup)

@bot.message_handler(content_types=['web_app_data'])
def handle_data(message):
    data = json.loads(message.web_app_data.data)
    db.add_contact(data.get('name'), data.get('time'), data.get('phone'))
    bot.send_message(message.chat.id, f"✅ Контакт {data.get('name')} сохранен!")