import threading
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controller.bot_logic import bot
from api.routes import router

app = FastAPI()

# 1. Вместо "*" лучше явно прописать адреса, 
# либо убрать allow_credentials=True, если оно тебе не нужно.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://vladmit1.github.io",
        "https://tracker.vladmit.org"
    ],
    allow_credentials=True, # Если это True, origins не может быть ["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

def run_bot():
    # Важный момент: если на первом компе бот работает через Webhook, 
    # то здесь polling может выбивать того бота. 
    # Убедись, что токены РАЗНЫЕ.
    print("🤖 Бот запущен (Long Polling)...")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)