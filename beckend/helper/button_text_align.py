from telebot import types

class AlignedMarkup:
    def __init__(self, row_width=2):
        self.buttons_data = [] 
        self.row_width = row_width

    def add(self, text, callback_data=None, url=None, web_app=None):
        self.buttons_data.append({
            "text": text.strip(),
            "callback_data": callback_data,
            "url": url,
            "web_app": web_app
        })

    def get_markup(self):
        markup = types.InlineKeyboardMarkup(row_width=self.row_width)
        
        if not self.buttons_data:
            return markup

        ready_buttons = []
        for b in self.buttons_data:
            # Создаем кнопку без лишних невидимых символов
            # Telegram сам отцентрирует текст идеально по середине
            ready_buttons.append(types.InlineKeyboardButton(
                text=b["text"],
                callback_data=b["callback_data"],
                url=b["url"],
                web_app=b["web_app"]
            ))

        markup.add(*ready_buttons)
        return markup