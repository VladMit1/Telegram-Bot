from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from database.db_manager import db
from modules.analytics import register_call

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/contacts")
async def get_contacts():
    return db.get_all_contacts()

@app.get("/api/stats")
async def get_stats():
    # Пример будущего модуля аналитики
    contacts = db.get_all_contacts()
    return {"total": len(contacts), "calls": sum(c['calls'] for c in contacts)}

@app.post("/api/call/{contact_id}")
async def make_call(contact_id: int):
    # Вызываем наш модуль аналитики
    result = register_call(contact_id)
    return result

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