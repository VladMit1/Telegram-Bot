import threading
import uvicorn
import sys
import os

# Путь для импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_logic import bot
from api.routes import app
from database.db_manager import db

def run_bot():
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)

def run_api():
    print("🌐 API запущен: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == '__main__':
    # 1. Проверка базы и вывод в консоль
    try:
        contacts = db.get_all_contacts()
        if not contacts:
            print("📝 База пуста, добавляю тест...")
            db.add_contact("Иван Проверка", "14:30", "+79001234567")
            contacts = db.get_all_contacts()

        print("\n" + "="*40)
        print("📋 ТЕКУЩИЕ КОНТАКТЫ В КОНСОЛИ:")
        for c in contacts:
            print(f"ID: {c['id']} | {c['name']} | Звонков: {c['calls']}")
        print("="*40 + "\n")
    except Exception as e:
        print(f"❌ Ошибка базы: {e}")

    # 2. Запуск потоков
    threading.Thread(target=run_bot, daemon=True).start()
    run_api()