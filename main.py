import telebot
import sqlite3
import json
import kb

TOKEN = "8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc"
bot = telebot.TeleBot(TOKEN)

# --- РАБОТА С БАЗОЙ ДАННЫХ ---
def init_db():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts 
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, time TEXT)
    ''')
    conn.commit()
    conn.close()

def save_to_db(name, time):
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO contacts (name, time) VALUES (?, ?)', (name, time))
    conn.commit()
    conn.close()

def get_history():
    conn = sqlite3.connect('tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, time FROM contacts ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    return rows
# ----------------------------

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "📱 Трекер активен. Нажми кнопку для записи:", 
        reply_markup=kb.main_menu()
    )

# ЛОВИМ ДАННЫЕ ИЗ MINI APP
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    data = json.loads(message.web_app_data.data) # Распаковываем JSON
    name = data['name']
    time = data['time']
    
    # Сохраняем в локальный файл .db
    save_to_db(name, time)
    
    # Формируем отчет из базы
    history = get_history()
    report = "✅ **Контакт сохранен!**\n\nПоследние записи:\n"
    for item in history:
        report += f"• {item[0]} — `{item[1]}`\n"
        
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

if __name__ == "__main__":
    init_db() # Создаем базу при запуске
    print("🚀 Бот с базой данных запущен...")
    bot.infinity_polling()