from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"

def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Каталог", callback_data='catalog')],
        [InlineKeyboardButton("Отзывы", callback_data='reviews')],
        [InlineKeyboardButton("О нас", callback_data='about')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    query.answer()
    
    if data == 'catalog':
        keyboard = [
            [InlineKeyboardButton("Мужская одежда", callback_data='mens')],
            [InlineKeyboardButton("Женская одежда", callback_data='womens')]
        ]
        query.edit_message_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data == 'reviews':
        query.edit_message_text("Отзывы пользователей скоро будут здесь 📝")

    elif data == 'about':
        query.edit_message_text("Мы — WhyResale. Лучшие люкс-реплики по честным ценам 💎")

def main():
    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
