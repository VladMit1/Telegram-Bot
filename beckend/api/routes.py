from fastapi import APIRouter
from database.db_manager import db
from controller.bot_logic import bot

router = APIRouter()

@router.get("/contacts")
def get_contacts():
    raw = db.get_all()
    return [{"id": r[0], "name": r[1], "phone": r[2], "time": r[3], "calls": r[4]} for r in raw]


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int):
    # Достаем ID сообщения бота из базы перед удалением записи
    info = db.get_contact_info(contact_id)
    if info:
        msg_id, chat_id = info
        try:
            # Удаляем сообщение-подтверждение из чата
            bot.delete_message(chat_id, msg_id)
            print(f"🗑️ Сообщение {msg_id} удалено из чата")
        except Exception as e:
            print(f"⚠️ Не удалось удалить в TG: {e}")
            
    db.delete_contact(contact_id)
    return {"status": "ok"}