from telebot import types

class AlignedMarkup:
    def __init__(self, row_width=2):
        self.buttons_data = [] # Храним (text, callback, url, web_app)
        self.row_width = row_width

    def add(self, text, callback_data=None, url=None, web_app=None):
        self.buttons_data.append({
            "text": text.strip(),
            "callback_data": callback_data,
            "url": url,
            "web_app": web_app
        })

    def _get_visual_weight(self, text):
        """ Считаем вес: эмодзи=2, остальное=1 """
        return sum(2 if ord(char) > 1000 else 1 for char in text)

    def get_markup(self):
        markup = types.InlineKeyboardMarkup(row_width=self.row_width)
        
        if not self.buttons_data:
            return markup

        # 1. Находим максимальный визуальный вес среди всех добавленных кнопок
        max_weight = max(self._get_visual_weight(b["text"]) for b in self.buttons_data)
        
        # 2. Добавляем небольшой запас (чтобы текст гарантированно прижался влево на ПК)
        # Для 2-х кнопок в ряд на ПК "золотое" значение веса — около 18-20
        target_weight = max(max_weight, 18 if self.row_width == 2 else 35)

        ready_buttons = []
        for b in self.buttons_data:
            current_w = self._get_visual_weight(b["text"])
            
            # Твоя формула: разница весов
            diff = target_weight - current_w
            
            # Добиваем невидимыми символами (каждый весит 2)
            filler = "ㅤ" * (diff // 2)
            # Если остался нечетный остаток, докидываем обычный пробел
            extra_space = " " if diff % 2 != 0 else ""
            
            aligned_text = f"{b['text']}{extra_space}{filler}"
            
            ready_buttons.append(types.InlineKeyboardButton(
                text=aligned_text,
                callback_data=b["callback_data"],
                url=b["url"],
                web_app=b["web_app"]
            ))

        # Раскладываем кнопки по рядам
        markup.add(*ready_buttons)
        return markup