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

@app.get("/api/contacts")
async def get_contacts():
    return db.get_all_contacts()

@app.post("/api/call/{contact_id}")
async def make_call(contact_id: int):
    db.increment_call(contact_id)
    return {"status": "success"}