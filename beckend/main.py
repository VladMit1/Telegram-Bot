import threading
import uvicorn
import telebot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Импорты
from config import TOKEN, DB_PATH
from service.finance_manager import FinanceManager
from controller.bot_logic import register_handlers
from api.routes import router

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

app.include_router(router, prefix="/api")

def run_bot():
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    # Запуск бота в потоке
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Запуск FastAPI
    print(f"🚀 API доступно на порту 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)