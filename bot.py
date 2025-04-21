import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import json
import os

API_TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# Хранилище для корзины
user_cart = {}

# Хранилище заказов
orders = []

# Товары
catalog = {
    'Обувь': [
        {'name': 'New balance 2002r', 'sizes': '36-45eu', 'price': '6000р', 'image': 'path_to_image1.jpg'},
        {'name': 'Dior b22', 'sizes': '36-45eu', 'price': '9900р', 'image': 'path_to_image2.jpg'},
        {'name': 'Dior b23', 'sizes': '36-45eu', 'price': '14900р', 'image': 'path_to_image3.jpg'},
        {'name': 'Prada Cloudbust Thunder', 'sizes': '36-45eu', 'price': '16900р', 'image': 'path_to_image4.jpg'},
        {'name': 'Yeezy boost 350', 'sizes': '36-45eu', 'price': '6190р', 'image': 'path_to_image5.jpg'}
    ],
    'Штаны/брюки/шорты': [
        {'name': 'Джинсы Balenciaga', 'sizes': 'S-XL', 'price': '7990р', 'image': 'path_to_image6.jpg'},
        {'name': 'Спортивные брюки Balenciaga Черные', 'sizes': 'S-XL', 'price': '9990р', 'image': 'path_to_image7.jpg'},
        {'name': 'Спортивные брюки Balenciaga Серые', 'sizes': 'S-XL', 'price': '9990р', 'image': 'path_to_image8.jpg'},
        {'name': 'Джинсовые брюки Vuja De', 'sizes': 'S-XL', 'price': '10990р', 'image': 'path_to_image9.jpg'}
    ]
}

# Стартовое меню
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Каталог', 'Отзывы', 'О нас')
    await message.answer("Добро пожаловать в наш магазин!", reply_markup=keyboard)

# Меню каталога
@dp.message_handler(lambda message: message.text == "Каталог")
async def show_catalog(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Обувь', 'Штаны/брюки/шорты', 'Назад')
    await message.answer("Выберите категорию:", reply_markup=keyboard)

# Обувь
@dp.message_handler(lambda message: message.text == "Обувь")
async def show_shoes(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Назад')
    for item in catalog['Обувь']:
        await message.answer(f"Название: {item['name']}\nРазмеры: {item['sizes']}\nЦена: {item['price']}", reply_markup=keyboard)
    await message.answer("Выберите товар, чтобы добавить в корзину.", reply_markup=keyboard)

# Штаны/брюки/шорты
@dp.message_handler(lambda message: message.text == "Штаны/брюки/шорты")
async def show_pants(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Назад')
    for item in catalog['Штаны/брюки/шорты']:
        await message.answer(f"Название: {item['name']}\nРазмеры: {item['sizes']}\nЦена: {item['price']}", reply_markup=keyboard)
    await message.answer("Выберите товар, чтобы добавить в корзину.", reply_markup=keyboard)

# Обработка кнопки назад
@dp.message_handler(lambda message: message.text == "Назад")
async def back_to_main(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Каталог', 'Отзывы', 'О нас')
    await message.answer("Вы вернулись в главное меню", reply_markup=keyboard)

# Добавление в корзину
@dp.message_handler(lambda message: message.text.startswith("Добавить в корзину"))
async def add_to_cart(message: types.Message):
    item_name = message.text.split(" ")[3:]  # Извлекаем название товара
    user_id = message.from_user.id
    if user_id not in user_cart:
        user_cart[user_id] = []
    user_cart[user_id].append(item_name)
    await message.answer(f"{item_name} добавлен в вашу корзину.")

# Просмотр корзины
@dp.message_handler(lambda message: message.text == "Корзина")
async def view_cart(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_cart and user_cart[user_id]:
        cart_items = "\n".join(user_cart[user_id])
        await message.answer(f"Ваши товары в корзине:\n{cart_items}")
    else:
        await message.answer("Ваша корзина пуста.")

# Подтверждение заказа
@dp.message_handler(lambda message: message.text == "Оформить заказ")
async def order_confirmation(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_cart and user_cart[user_id]:
        order_details = "\n".join(user_cart[user_id])
        await message.answer(f"Вы хотите оформить заказ на следующие товары:\n{order_details}\n\nПожалуйста, подтвердите, чтобы продолжить.")
        await message.answer("Введите ваши данные для анкеты: ФИО, адрес доставки, телефон.")
    else:
        await message.answer("Ваша корзина пуста. Добавьте товары в корзину.")

# Запись данных анкеты
@dp.message_handler(lambda message: message.text != "Оформить заказ")
async def collect_order_data(message: types.Message):
    user_id = message.from_user.id
    if message.text:
        orders.append({
            "user_id": user_id,
            "order_details": user_cart.get(user_id, []),
            "order_data": message.text
        })
        # Отправка уведомления владельцу
        await bot.send_message('@whyresale', f"Новый заказ: {message.text}\n{user_cart.get(user_id, [])}")
        await message.answer("Спасибо за заказ! Мы получим ваши данные.")
        user_cart[user_id] = []  # Очищаем корзину
    else:
        await message.answer("Введите корректные данные анкеты.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
