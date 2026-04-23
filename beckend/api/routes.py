from fastapi import APIRouter
from fastapi import HTTPException
from typing import Optional
from database.db_manager import db
from controller.bot_logic import TOKEN # Импортируем токен из логики бота
from pydantic import BaseModel
router = APIRouter()
# Схема данных для валидации (чтобы Python понимал JSON)
class LessonSchema(BaseModel):
    student_id: int|None
    date: str | None
    time: str|None
    topic: str = "Урок"
    duration: int

class ProgressUpdate(BaseModel):
    last_book: Optional[str] = None
    last_page: Optional[int] = None
    balance: Optional[int] = None
    lesson_price: Optional[int] = None

class PaymentSchema(BaseModel):
    student_id: int
    amount: int
    date: str

@router.post("/payments")
def create_payment(data: PaymentSchema):
    success = db.add_payment(data.student_id, data.amount, data.date)
    return {"status": "ok" if success else "error"}

@router.delete("/payments/{payment_id}")
def delete_payment_api(payment_id: int, data: dict):
    # data содержит student_id и amount для корректировки баланса
    success = db.delete_payment(payment_id, data['studentId'], data['amount'])
    if success:
        return {"status": "ok"}
    raise HTTPException(status_code=400, detail="Ошибка удаления")

@router.get("/contacts")
def get_contacts():
    # Передаем токен, чтобы менеджер базы мог создать ссылки на фото
    return db.get_contacts_for_api(TOKEN)




@router.post("/lessons")
def create_lesson(data: LessonSchema):
    success = db.add_lesson(
        data.student_id, 
        data.date, 
        data.time, 
        data.topic,
        data.duration
    )
    return {"status": "ok" if success else "error"}    

@router.patch("/contacts/{student_id}")
def update_student_progress(student_id: int, data: ProgressUpdate):
    # Превращаем модель в словарь, исключая пустые поля
    update_data = data.dict(exclude_unset=True)
    
    if not update_data:
        return {"status": "no data to update"}, 400
        
    success = db.universal_update_contact(student_id, update_data)
    
    if success:
        return {"status": "success"}
    return {"status": "error"}, 400

@router.get("/lessons")
def read_lessons():
    return db.get_all_lessons()

@router.delete("/lessons/{lesson_id}")
def delete_lesson(lesson_id: int):
    success = db.delete_lesson(lesson_id) # Реализуй этот метод в DBManager (DELETE FROM lessons WHERE id=?)
    return {"status": "ok" if success else "error"}

@router.patch("/lessons/{lesson_id}")
def update_lesson(lesson_id: int, data: dict):
    # Метод для переноса даты или времени
    success = db.update_lesson(lesson_id, data) 
    return {"status": "ok"}