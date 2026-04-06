import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.bot_logic import bot
from api.routes import router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router, prefix="/api")

def run_bot():
    print("🤖 Бот запущен...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    print("🌐 API сервер запущен на порту 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)