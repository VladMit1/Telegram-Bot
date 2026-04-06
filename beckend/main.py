import threading
import uvicorn
import sys
import os

# Добавляем текущую директорию в путь, чтобы Python видел модули внутри backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from controller.bot_logic import bot
from api.routes import app

def run_bot():
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)

def run_api():
    print("🌐 API запущен: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    # Поток для бота
    threading.Thread(target=run_bot, daemon=True).start()
    # Основной поток для API
    run_api()