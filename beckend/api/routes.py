from fastapi import APIRouter
from database.db_manager import db
from controller.bot_logic import TOKEN # Импортируем токен из логики бота

router = APIRouter()

@router.get("/contacts")
def get_contacts():
    # Передаем токен, чтобы менеджер базы мог создать ссылки на фото
    return db.get_contacts_for_api(TOKEN)

@router.delete("/contacts/{phone}")
def delete_contact(phone: str):
    db.delete_contact_by_phone(phone)
    return {"status": "ok"}