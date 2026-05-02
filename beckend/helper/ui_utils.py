import json
import os

FILE_PATH = 'last_messages.json'

def save_last_msg(chat_id, msg_id):
    try:
        data = {}
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[str(chat_id)] = msg_id
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Ошибка сохранения ID: {e}")

def delete_last_msg(bot, chat_id):
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            last_id = data.get(str(chat_id))
            if last_id:
                bot.delete_message(chat_id, last_id)
    except Exception:
        pass