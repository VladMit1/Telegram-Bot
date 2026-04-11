from fastapi import APIRouter
from database.db_manager import db

router = APIRouter()

@router.get("/contacts")
def get_contacts():
    return db.get_contacts_for_api()

@router.delete("/contacts/{phone}")
def delete_contact(phone: str):
    db.delete_contact_by_phone(phone)
    return {"status": "ok"}