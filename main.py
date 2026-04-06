import telebot
import kb

# Твой токен
TOKEN = "8709390336:AAFjZsd1FTPOtBbvJEl5KSouwiZgawHMYyc"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    # Мгновенно удаляем сообщение /start от пользователя для чистоты чата
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        print(f"Ошибка удаления: {e}")

    # Отправляем приветствие с кнопкой запуска приложения
    bot.send_message(
        message.chat.id, 
        "📱 **Трекер звонков готов**\nНажми на кнопку ниже, чтобы войти.", 
        reply_markup=kb.main_menu(),
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("📡 Бот запущен и ждет нажатий...")
    bot.infinity_polling()