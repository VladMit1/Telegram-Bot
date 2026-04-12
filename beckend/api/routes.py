from fastapi import APIRouter
from database.db_manager import db
from controller.bot_logic import TOKEN # Импортируем токен из логики бота
from pydantic import BaseModel
router = APIRouter()
# Схема данных для валидации (чтобы Python понимал JSON)
class LessonSchema(BaseModel):
    student_id: int
    date: str
    time: str
    topic: str = "Урок"

@router.get("/contacts")
def get_contacts():
    # Передаем токен, чтобы менеджер базы мог создать ссылки на фото
    return db.get_contacts_for_api(TOKEN)

@router.delete("/contacts/{phone}")
def delete_contact(phone: str):
    db.delete_contact_by_phone(phone)
    return {"status": "ok"}


@router.post("/lessons")
def create_lesson(data: LessonSchema):
    success = db.add_lesson(
        data.student_id, 
        data.date, 
        data.time, 
        data.topic
    )
    return {"status": "ok" if success else "error"}    