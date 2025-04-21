import json
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters, ConversationHandler
)

logging.basicConfig(level=logging.INFO)

# === ДАННЫЕ ===
TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"
ADMIN_USERNAME = "@whyresale"
ORDERS_FILE = "orders.json"

# Пример товаров
ITEMS = [
    {"id": "1", "name": "Nike Air Max", "price": "9000₽"},
    {"id": "2", "name": "Stone Island Pants", "price": "8500₽"}
]

# === СТАНЫ АНКЕТЫ ===
(ASK_NAME, ASK_ADDRESS, ASK_PHONE, WAITING_FOR_SCREENSHOT) = range(4)

user_cart = {}
user_forms = {}

# === КОМАНДЫ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton(f"{item['name']} - {item['price']}", callback_data=f"add_{item['id']}")]
        for item in ITEMS
    ]
    await update.message.reply_text("Добро пожаловать! Выберите товар:", reply_markup=InlineKeyboardMarkup(buttons))


async def cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart_items = user_cart.get(user_id, [])
    if not cart_items:
        await update.message.reply_text("Ваша корзина пуста.")
        return

    text = "🛒 Ваша корзина:\n"
    buttons = []
    for item in cart_items:
        text += f"• {item['name']} - {item['price']}\n"
        buttons.append([InlineKeyboardButton(f"❌ Удалить {item['name']}", callback_data=f"remove_{item['id']}")])

    buttons.append([InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")])
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("add_"):
        item_id = query.data.split("_")[1]
        item = next((i for i in ITEMS if i["id"] == item_id), None)
        if item:
            user_cart.setdefault(user_id, []).append(item)
            await query.edit_message_text(f"{item['name']} добавлен в корзину.")

    elif query.data.startswith("remove_"):
        item_id = query.data.split("_")[1]
        cart = user_cart.get(user_id, [])
        user_cart[user_id] = [i for i in cart if i["id"] != item_id]
        await query.edit_message_text("Товар удалён из корзины.")

    elif query.data == "checkout":
        await query.edit_message_text("Введите ваше ФИО:")
        return ASK_NAME


# === АНКЕТА ===
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_forms[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("Введите адрес доставки:")
    return ASK_ADDRESS


async def ask_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_forms[update.effective_user.id]["address"] = update.message.text
    await update.message.reply_text("Введите номер телефона:")
    return ASK_PHONE


async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_forms[update.effective_user.id]["phone"] = update.message.text
    await update.message.reply_text(
        "Почти готово! Переведите сумму по реквизитам:\n\n"
        "💳 СБЕРБАНК Попов Б.А\n"
        "📄 Номер счёта: 40817810738129310987\n"
        "💳 Номер карты: 2202 2081 3069 2370\n\n"
        "Затем отправьте скриншот оплаты."
    )
    return WAITING_FOR_SCREENSHOT


async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    form = user_forms.get(user_id)
    cart = user_cart.get(user_id, [])

    if not form or not cart:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")
        return ConversationHandler.END

    order = {
        "user": update.effective_user.username,
        "cart": cart,
        "form": form,
    }

    # Сохраняем заказ
    try:
        if not os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, "w") as f:
                json.dump([], f)
        with open(ORDERS_FILE, "r+") as f:
            orders = json.load(f)
            orders.append(order)
            f.seek(0)
            json.dump(orders, f, indent=2)
    except Exception as e:
        logging.error(f"Ошибка сохранения заказа: {e}")

    # Уведомление админу
    screenshot_file_id = update.message.photo[-1].file_id if update.message.photo else None
    admin_text = (
        f"📦 Новый заказ от @{update.effective_user.username}:\n"
        f"📝 ФИО: {form['name']}\n"
        f"🏠 Адрес: {form['address']}\n"
        f"📞 Телефон: {form['phone']}\n"
        f"🛒 Корзина:\n" +
        "\n".join([f" - {item['name']} ({item['price']})" for item in cart])
    )

    await context.bot.send_message(chat_id=ADMIN_USERNAME, text=admin_text)
    if screenshot_file_id:
        await context.bot.send_photo(chat_id=ADMIN_USERNAME, photo=screenshot_file_id)

    await update.message.reply_text("Спасибо за заказ! Мы свяжемся с вами в ближайшее время.")
    user_cart[user_id] = []
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оформление заказа отменено.")
    return ConversationHandler.END


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cart", cart))
    app.add_handler(CallbackQueryHandler(handle_callback))

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_callback, pattern="^checkout$")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            WAITING_FOR_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
