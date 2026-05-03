import traceback

def safe_handler(bot):
   def decorator(func):    
        def wrapper(call_or_message, *args, **kwargs):
            try:
                return func(call_or_message, *args, **kwargs)
            except Exception as e:
               # 1. Печатаем КРАСИВУЮ ошибку в консоль
               print("\n" + "!"*40)
               print(f"🔥 ERROR В ФУНКЦИИ: {func.__name__}")
               print(f"Тип ошибки: {type(e).__name__}")
               print(f"Текст: {e}")
               print("-" * 20)
               traceback.print_exc()
               print("!"*40 + "\n")

               # 2. Уведомляем пользователя (или тебя), что всё пошло не так
               chat_id = call_or_message.message.chat.id if hasattr(call_or_message, 'message') else call_or_message.chat.id
               bot.send_message(chat_id, f"⚠️ <b>Ошибка в коде:</b>\n<code>{e}</code>", parse_mode="HTML")
               
               # Если это кнопка — убираем "часики"
               if hasattr(call_or_message, 'data'):
                  bot.answer_callback_query(call_or_message.id)
                  
            return wrapper
   return decorator