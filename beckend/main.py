import threading
import uvicorn
import sys
import os

# Добавляем путь к backend, чтобы импорты работали корректно
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controller.bot_logic import bot
from api.routes import app
from database.db_manager import db  # ОБЯЗАТЕЛЬНО ИМПОРТИРУЕМ DB

def run_bot():
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)

def run_api():
    print("🌐 API запущен: http://localhost:8000")
    # Параметр log_level поможет видеть запросы в консоли
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == '__main__':
    # 1. Сначала проверяем/наполняем базу (ДО запуска серверов)
    try:
        contacts = db.get_all_contacts()
        if not contacts:
            print("📝 База пуста, добавляю тестовый контакт...")
            db.add_contact("Иван Проверка", "14:30", "+79001234567")
        else:
            print(f"📊 В базе уже есть контактов: {len(contacts)}")
    except Exception as e:
        print(f"❌ Ошибка при работе с базой: {e}")

    # 2. Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 3. Запускаем API в основном потоке (он будет держать программу запущенной)
    run_api()