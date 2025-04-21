import json
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"
ADMIN_USERNAME = "@whyresale"
ORDERS_FILE = "orders.json"

# Каталог товаров
catalog = {
    "Штаны": [
        {
            "id": "pants_1",
            "name": "Fear of God Essentials Pants",
            "description": "Oversized fit, premium quality replica",
            "photo": "https://i.imgur.com/WQFEfYJ.jpg"
        }
    ],
    "Обувь": [
        {
            "id": "shoes_1",
            "name": "New Balance 9060 Grey",
            "description": "Top quality rep. Very comfortable and stylish",
            "photo": "https://i.imgur.com/C2MNUGB.jpg"
        }
    ]
}

# Хранилище корзин и заказов
user_carts = {}
user_order_data = {}

# ──────────────────────────────────────────────────────────────
# Клавиатуры

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("💬 Отзывы", callback_data="reviews")],
        [InlineKeyboardButton("ℹ️ О нас", callback_data="about")]
    ])

def catalog_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👖 Штаны", callback_data="category_Штаны")],
        [InlineKeyboardButton("👟 Обувь", callback_data="category_Обувь")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ])

def back_to_catalog_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="catalog")]])

def cart_keyboard(user_id):
    cart = user_carts.get(user_id, [])
    keyboard = []
    for item in cart:
        keyboard.append([InlineKeyboardButton(f"🗑 Удалить {item['name']}", callback_data=f"remove_{item['id']}")])
    if cart:
        keyboard.append([InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

# ──────────────────────────────────────────────────────────────
# Команды

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите раздел:", reply_markup=main_menu_keyboard())

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "catalog":
        await query.edit_message_text("Выберите категорию:", reply_markup=catalog_keyboard())

    elif query.data == "back_to_main":
        await query.edit_message_text("Выберите раздел:", reply_markup=main_menu_keyboard())

    elif query.data.startswith("category_"):
        category = query.data.split("_")[1]
        items = catalog.get(category, [])
        for item in items:
            text = f"{item['name']}\n\n{item['description']}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ В корзину", callback_data=f"add_{item['id']}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="catalog")]
            ])
            await context.bot.send_photo(chat_id=query.message.chat.id, photo=item["photo"], caption=text, reply_markup=keyboard)

    elif query.data.startswith("add_"):
        item_id = query.data.split("_", 1)[1]
        for category_items in catalog.values():
            for item in category_items:
                if item["id"] == item_id:
                    user_carts.setdefault(user_id, []).append(item)
                    await query.answer("Добавлено в корзину!")
                    return

    elif query.data.startswith("remove_"):
        item_id = query.data.split("_", 1)[1]
        cart = user_carts.get(user_id, [])
        user_carts[user_id] = [item for item in cart if item["id"] != item_id]
        await query.edit_message_text("Обновлённая корзина:", reply_markup=cart_keyboard(user_id))

    elif query.data == "checkout":
        await query.message.reply_text("Введите ФИО:")
        return ASK_NAME

    elif query.data == "reviews":
        await query.edit_message_text("💬 Отзывы\n\nЗдесь будут отзывы клиентов.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]))

    elif query.data == "about":
        await query.edit_message_text("ℹ️ О нас\n\nМагазин люкс-реплик Why Resale.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]]))

# ──────────────────────────────────────────────────────────────
# /cart

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = user_carts.get(user_id, [])
    if not cart:
        await update.message.reply_text("🛒 Ваша корзина пуста.")
    else:
        text = "🛒 Ваша корзина:\n\n"
        for item in cart:
            text += f"- {item['name']}\n"
        await update.message.reply_text(text, reply_markup=cart_keyboard(user_id))

# ──────────────────────────────────────────────────────────────
# Оформление заказа

ASK_NAME, ASK_ADDRESS, ASK_PHONE, ASK_SCREENSHOT = range(4)

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_order_data[update.effective_user.id] = {"name": update.message.text}
    await update.message.reply_text("Введите адрес доставки:")
    return ASK_ADDRESS

async def ask_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_order_data[update.effective_user.id]["address"] = update.message.text
    await update.message.reply_text("Введите номер телефона:")
    return ASK_PHONE

async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_order_data[update.effective_user.id]["phone"] = update.message.text
    await update.message.reply_text(
        "✅ Отлично!\n\nОтправьте скриншот оплаты на реквизиты:\n\n"
        "💳 СБЕРБАНК Попов Б.А\n"
        "Номер счёта: 40817810738129310987\n"
        "Номер карты: 2202 2081 3069 2370\n\n"
        "📸 Пришлите скрин:"
    )
    return ASK_SCREENSHOT

async def receive_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    order = user_order_data[user_id]
    cart = user_carts.get(user_id, [])

    # Сохраняем в файл
    all_orders = []
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, "r") as f:
            all_orders = json.load(f)
    all_orders.append({"user_id": user_id, "order": order, "cart": cart})
    with open(ORDERS_FILE, "w") as f:
        json.dump(all_orders, f, indent=2)

    # Отправляем админу
    caption = (
        f"📦 Новый заказ от @{update.effective_user.username}:\n\n"
        f"👤 ФИО: {order['name']}\n"
        f"🏠 Адрес: {order['address']}\n"
        f"📞 Телефон: {order['phone']}\n\n"
        f"🛒 Корзина:\n" +
        "\n".join(f"- {item['name']}" for item in cart)
    )
    photo = update.message.photo[-1].file_id
    await context.bot.send_photo(chat_id=ADMIN_USERNAME, photo=photo, caption=caption)

    await update.message.reply_text("✅ Спасибо! Ваш заказ оформлен.", reply_markup=main_menu_keyboard())

    # Очистка
    user_carts.pop(user_id, None)
    user_order_data.pop(user_id, None)
    return ConversationHandler.END

# ──────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cart", show_cart))
    app.add_handler(CallbackQueryHandler(handle_buttons))

    convo = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_buttons, pattern="^checkout$")],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name)],
            ASK_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
            ASK_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_phone)],
            ASK_SCREENSHOT: [MessageHandler(filters.PHOTO, receive_screenshot)],
        },
        fallbacks=[],
    )
    app.add_handler(convo)

    app.run_polling()

if __name__ == "__main__":
    main()
