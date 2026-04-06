from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db_manager import db

app = FastAPI()

# Разрешаем запросы с GitHub и Localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/contacts")
async def add_contact_from_web(request: Request):
    data = await request.json()
    name = data.get("name")
    phone = data.get("phone")
    time = data.get("time", "12:00")
    
    # Сохраняем в нашу SQLite базу
    db.add_contact(name, time, phone)
    
    print(f"✅ Добавлен новый контакт: {name} ({phone})")
    return {"status": "success", "added": name}

@app.post("/api/call/{contact_id}")
async def make_call(contact_id: int):
    db.increment_call(contact_id)
    return {"status": "success"}