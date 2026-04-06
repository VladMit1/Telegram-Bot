from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db_manager import db

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