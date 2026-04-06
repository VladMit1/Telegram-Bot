from database.db_manager import db

def register_call(contact_id: int):
    """Увеличивает счетчик звонков для конкретного контакта"""
    cursor = db.conn.cursor()
    cursor.execute(
        'UPDATE contacts SET calls_count = calls_count + 1 WHERE id = ?', 
        (contact_id,)
    )
    db.conn.commit()
    return {"status": "success", "new_count": get_contact_calls(contact_id)}

def get_contact_calls(contact_id: int):
    cursor = db.conn.cursor()
    cursor.execute('SELECT calls_count FROM contacts WHERE id = ?', (contact_id,))
    res = cursor.fetchone()
    return res[0] if res else 0