import os
import json
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text

BOT_TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"
API_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Структура каталога товаров
catalog = {
    'Штаны/брюки': [
        {'name': 'Джинсы Balenciaga', 'size': 'S-XL', 'price': '7990р', 'image': 'url_1'},
        {'name': 'Спортивные брюки Balenciaga С двойной талией Черного цвета', 'size': 'S-XL', 'price': '9990р', 'image': 'url_2'},
        {'name': 'Спортивные брюки Balenciaga с двойной талией Серого цвета', 'size': 'S-XL', 'price': '9990р', 'image': 'url_3'},
        {'name': 'Джинсовые брюки Vuja De Diviser наизнанку', 'size': 'S-XL', 'price': '10990р', 'image': 'url_4'}
    ],
    'Обувь': [
        {'name': 'New balance 2002r', 'size': '36-45eu', 'price': '6000р', 'image': 'url_5'},
        {'name': 'Dior b22', 'size': '36-45eu', 'price': '9900р', 'image': 'url_6'},
        {'name': 'Dior b23', 'size': '36-45eu', 'price': '14900р', 'image': 'url_7'},
        {'name': 'Кроссовки Prada Cloudbust Thunder', 'size': '36-45eu', 'price': '16900р', 'image': 'url_8'},
        {'name': 'Yeezy boost 350', 'size': '36-45eu', 'price': '6190р', 'image': 'url_9'}
    ]
}

# Корзина покупок по user_id
user_cart = {}

# Начальная команда /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Каталог")
    item2 = types.KeyboardButton("Отзывы")
    item3 = types.KeyboardButton("О нас")
    markup.add(item1, item2, item3)
    await message.answer("Привет! Я помогу тебе с покупками.", reply_markup=markup)

# Навигация по каталогу
async def show_catalog(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Штаны/брюки")
    item2 = types.KeyboardButton("Обувь")
    item3 = types.KeyboardButton("Назад")
    markup.add(item1, item2, item3)
    await message.answer("Выберите категорию:", reply_markup=markup)

# Показываем товары из категории
async def show_items(message: types.Message, category: str):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    items = catalog.get(category, [])
    for item in items:
        markup.add(types.KeyboardButton(item['name']))
    item_back = types.KeyboardButton("Назад")
    item_cart = types.KeyboardButton("Перейти в корзину")
    markup.add(item_back, item_cart)

    items_text = "\n".join([f"{item['name']} - {item['price']}" for item in items])
    await message.answer(f"Товары в категории {category}:\n{items_text}", reply_markup=markup)

# Добавить товар в корзину
@dp.message_handler(Text(equals="Добавить в корзину"))
async def add_to_cart(message: types.Message):
    item_name = message.text.strip()  # Имя товара
    user_id = message.from_user.id

    if user_id not in user_cart:
        user_cart[user_id] = []

    user_cart[user_id].append(item_name)
    await message.answer(f"{item_name} добавлен в корзину!")

# Показать корзину
async def show_cart(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_cart and user_cart[user_id]:
        cart_items = "\n".join(user_cart[user_id])
        await message.answer(f"Ваша корзина:\n{cart_items}")
    else:
        await message.answer("Ваша корзина пуста!")

# Удалить товар из корзины
@dp.message_handler(Text(equals="Удалить из корзины"))
async def remove_from_cart(message: types.Message):
    item_name = message.text.strip()  # Имя товара
    user_id = message.from_user.id
    if user_id in user_cart and item_name in user_cart[user_id]:
        user_cart[user_id].remove(item_name)
        await message.answer(f"{item_name} удален из корзины.")
    else:
        await message.answer(f"{item_name} нет в корзине.")

# Подтверждение заказа
@dp.message_handler(Text(equals="Оформить заказ"))
async def confirm_order(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_cart or not user_cart[user_id]:
        await message.answer("Ваша корзина пуста. Пожалуйста, добавьте товары в корзину.")
        return

    # Анкета
    markup = types.ReplyKeyboardRemove()
    await message.answer("Пожалуйста, предоставьте следующие данные:\n1. ФИО\n2. Адрес доставки\n3. Номер телефона", reply_markup=markup)
    await message.answer("После того как заполните, отправьте ваши данные и скриншот оплаты.", reply_markup=markup)

# Обработчик данных анкеты
@dp.message_handler(lambda message: message.text)
async def handle_order_details(message: types.Message):
    user_id = message.from_user.id
    user_data = message.text

    # Отправка данных на аккаунт @whyresale
    await bot.send_message('@whyresale', f"Новый заказ от {message.from_user.username}:\n{user_data}")

    # Очистить корзину
    user_cart[user_id] = []

    await message.answer("Спасибо за заказ! Ваш заказ отправлен. Мы свяжемся с вами для подтверждения.")

# Обработчик команды "Каталог"
@dp.message_handler(Text(equals="Каталог"))
async def catalog_command(message: types.Message):
    await show_catalog(message)

# Обработчик кнопки "Штаны/брюки" и "Обувь"
@dp.message_handler(Text(equals="Штаны/брюки"))
async def catalog_pants(message: types.Message):
    await show_items(message, "Штаны/брюки")

@dp.message_handler(Text(equals="Обувь"))
async def catalog_shoes(message: types.Message):
    await show_items(message, "Обувь")

# Обработчик кнопки "Назад"
@dp.message_handler(Text(equals="Назад"))
async def back_command(message: types.Message):
    await show_catalog(message)

# Обработчик кнопки "Перейти в корзину"
@dp.message_handler(Text(equals="Перейти в корзину"))
async def go_to_cart(message: types.Message):
    await show_cart(message)

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
