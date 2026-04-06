from telebot import types

# Ссылка на твой GitHub Pages (которую ты получишь на следующем этапе)
# Пока можешь оставить заглушку, но потом обязательно замени!
URL = "https://vladimir.github.io/call-tracker/" 

def main_menu():
    """Создает инлайн-кнопку для запуска Mini App"""
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(URL)
    btn = types.InlineKeyboardButton(text="🚀 Открыть Трекер", web_app=web_app)
    markup.add(btn)
    return markup