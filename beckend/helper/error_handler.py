import traceback
from functools import wraps

def safe_handler(bot):
    def decorator(func):
        @wraps(func) # Чтобы функции сохраняли свои имена для логов
        def wrapper(call_or_message, *args, **kwargs):
            try:
                return func(call_or_message, *args, **kwargs)
            except Exception as e:
                # 1. Логи в консоль
                print("\n" + "!"*50)
                print(f"🔥 ERROR В ФУНКЦИИ: {func.__name__}")
                print(f"Тип: {type(e).__name__}")
                print(f"Текст: {e}")
                print("-" * 30)
                traceback.print_exc()
                print("!"*50 + "\n")

                # 2. Определяем chat_id
                if hasattr(call_or_message, 'message'):
                    chat_id = call_or_message.message.chat.id
                else:
                    chat_id = call_or_message.chat.id

                # 3. Уведомляем пользователя
                try:
                    bot.send_message(chat_id, f"⚠️ <b>Системная ошибка:</b>\n<code>{e}</code>", parse_mode="HTML")
                    
                    if hasattr(call_or_message, 'data'):
                        bot.answer_callback_query(call_or_message.id)
                except:
                    pass # Чтобы сам обработчик ошибок не упал
            
        return wrapper
    return decorator