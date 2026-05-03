import threading
import uvicorn
import telebot
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты
from config import TOKEN, DB_PATH
from service.finance_manager import FinanceManager
from controller.bot_logic import register_handlers

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в .env!")
# 1. Инициализация объектов
bot = telebot.TeleBot(TOKEN)
finance = FinanceManager(DB_PATH)

# 2. Регистрация логики бота
register_handlers(bot, finance)

# 3. Настройка FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # На время тестов можно оставить так
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def run_bot():
    print("🤖 Бот запущен и ожидает сеть...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"❌ Ошибка подключения бота: {e}")
            time.sleep(10)  # Подождать 10 секунд перед следующей попыткой

if __name__ == "__main__":
    # Запуск бота в потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запуск FastAPI
    print(f"🚀 API доступно на порту 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)