import telebot
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db_manager import db

# --- НАСТРОЙКИ БОТА ---
TOKEN = '8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc'
bot = telebot.TeleBot(TOKEN)
URL_APP = "https://vladmit1.github.io/Telegram-Bot/"

@bot.message_handler(commands=['start'])
def start(message):
    # Устанавливаем кнопку меню слева от ввода
    bot.set_chat_menu_button(message.chat.id, telebot.types.MenuButtonWebApp("Список учеников", telebot.types.WebAppInfo(url=URL_APP)))
    
    # Кнопка над клавиатурой
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("➕ Добавить ученика", request_contact=True))
    
    bot.send_message(message.chat.id, "Кнопка 'Список учеников' закреплена внизу! Присылай контакты для добавления.", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    c = message.contact
    name = f"{c.first_name} {c.last_name or ''}".strip()
    if db.add_contact(name, "12:00", c.phone_number):
        bot.send_message(message.chat.id, f"✅ {name} добавлен в список.")
    else:
        bot.send_message(message.chat.id, f"ℹ️ {name} уже есть в списке.")

# --- API ---
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/api/contacts")
def get_contacts():
    return db.get_all_contacts()

@app.delete("/api/contacts/{contact_id}")
def delete_contact(contact_id: int):
    db.delete_contact(contact_id)
    return {"status": "deleted"}

# Запуск бота в отдельном потоке обычно делается через threading, 
# но для теста просто запусти bot.polling() после app