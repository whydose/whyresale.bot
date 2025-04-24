import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import json
import os

API_TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
        {'name': 'New balance 2002r', 'sizes': '36-45eu', 'price': '6000р', 'image': os.path.join(BASE_DIR, 'images', 'New-balance-2002r.png'},
        {'name': 'Dior b22', 'sizes': '36-45eu', 'price': '9900р', 'image': os.path.join(BASE_DIR, 'images', 'Dior-B22.png'},
        {'name': 'Dior b23', 'sizes': '36-45eu', 'price': '14900р', 'image': os.path.join(BASE_DIR, 'images', 'Dior-b23.jpg'},
        {'name': 'Prada Cloudbust Thunder', 'sizes': '36-45eu', 'price': '16900р', 'image': os.path.join(BASE_DIR, 'images', 'Prada-Cloudbust-Thunder.jpg.webp'},
        {'name': 'Yeezy boost 350', 'sizes': '36-45eu', 'price': '6190р', 'image': os.path.join(BASE_DIR, 'images', 'Yeezy-boost-350.jpg'}
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
    keyboard.add('Каталог', 'Корзина', 'Отзывы', 'О нас')
    await message.answer("Добро пожаловать в наш магазин!", reply_markup=keyboard)

# Меню каталога
@dp.message_handler(lambda message: message.text == "Каталог")
async def show_catalog(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Обувь', 'Штаны/брюки/шорты', 'Корзина', 'Назад')
    await message.answer("Выберите категорию:", reply_markup=keyboard)

# Обувь
@dp.message_handler(lambda message: message.text == "Обувь")
async def show_shoes(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Корзина', 'Назад')
    
    for item in catalog['Обувь']:
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("Добавить в корзину", callback_data=f"add_{item['name']}"))
        
        try:
            with open(item['image'], 'rb') as photo:
                await message.answer_photo(
                    photo,
                    caption=f"Название: {item['name']}\nРазмеры: {item['sizes']}\nЦена: {item['price']}",
                    reply_markup=inline_kb
                )
        except FileNotFoundError:
            await message.answer(
                f"Название: {item['name']}\nРазмеры: {item['sizes']}\nЦена: {item['price']}\n[Изображение недоступно]",
                reply_markup=inline_kb
            )
    
    await message.answer("Выберите товар, чтобы добавить в корзину.", reply_markup=keyboard)

# Штаны/брюки/шорты
@dp.message_handler(lambda message: message.text == "Штаны/брюки/шорты")
async def show_pants(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Корзина', 'Назад')
    
    for item in catalog['Штаны/брюки/шорты']:
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("Добавить в корзину", callback_data=f"add_{item['name']}"))
        
        await message.answer(
            f"Название: {item['name']}\nРазмеры: {item['sizes']}\nЦена: {item['price']}",
            reply_markup=inline_kb
        )
    
    await message.answer("Выберите товар, чтобы добавить в корзину.", reply_markup=keyboard)

# Обработка кнопки назад
@dp.message_handler(lambda message: message.text == "Назад")
async def back_to_main(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add('Каталог', 'Корзина', 'Отзывы', 'О нас')
    await message.answer("Вы вернулись в главное меню", reply_markup=keyboard)

# Обработка inline кнопок
@dp.callback_query_handler(lambda c: c.data.startswith('add_'))
async def process_callback_add_to_cart(callback_query: types.CallbackQuery):
    item_name = callback_query.data[4:]
    user_id = callback_query.from_user.id
    
    if user_id not in user_cart:
        user_cart[user_id] = []
    
    user_cart[user_id].append(item_name)
    await bot.answer_callback_query(callback_query.id, text=f"{item_name} добавлен в корзину!")

@dp.callback_query_handler(lambda c: c.data.startswith('remove_'))
async def process_callback_remove_from_cart(callback_query: types.CallbackQuery):
    item_name = callback_query.data[7:]
    user_id = callback_query.from_user.id
    
    if user_id in user_cart and item_name in user_cart[user_id]:
        user_cart[user_id].remove(item_name)
        await bot.answer_callback_query(callback_query.id, text=f"{item_name} удален из корзины!")
    else:
        await bot.answer_callback_query(callback_query.id, text="Товар не найден в корзине!")

# Просмотр корзины
@dp.message_handler(lambda message: message.text == "Корзина")
async def view_cart(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_cart and user_cart[user_id]:
        cart_text = "Ваша корзина:\n\n"
        for item in user_cart[user_id]:
            cart_text += f"• {item}\n"
        
        cart_text += "\nВыберите действие:"
        
        keyboard = InlineKeyboardMarkup()
        for item in set(user_cart[user_id]):  # Уникальные товары
            keyboard.add(InlineKeyboardButton(f"Удалить {item}", callback_data=f"remove_{item}"))
        
        keyboard.add(InlineKeyboardButton("Оформить заказ", callback_data="checkout"))
        
        await message.answer(cart_text, reply_markup=keyboard)
    else:
        await message.answer("Ваша корзина пуста.")

# Оформление заказа
@dp.callback_query_handler(lambda c: c.data == 'checkout')
async def process_checkout(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    
    if user_id in user_cart and user_cart[user_id]:
        payment_info = """
        Реквизиты для оплаты:
        
        СБЕРБАНК
        Попов Б.А
        Номер счета: 40817810738129310987
        Номер карты: 2202208130692370
        
        После оплаты пришлите скриншот чека вместе с заполненной анкетой:
        
        ФИО: 
        Адрес доставки: 
        Номер телефона: 
        """
        
        await bot.send_message(user_id, payment_info)
        await bot.send_message(user_id, "Пожалуйста, заполните анкету и отправьте ее вместе со скриншотом оплаты.")
    else:
        await bot.send_message(user_id, "Ваша корзина пуста. Невозможно оформить заказ.")

# Обработка анкеты и скриншота
@dp.message_handler(content_types=['text', 'photo'])
async def handle_documents(message: types.Message):
    user_id = message.from_user.id
    
    if user_id in user_cart and user_cart[user_id]:
        if message.text and all(x in message.text for x in ['ФИО:', 'Адрес доставки:', 'Номер телефона:']):
            # Это анкета
            order_details = {
                "user_id": user_id,
                "username": message.from_user.username,
                "items": user_cart[user_id],
                "form_data": message.text,
                "payment_screenshot": None
            }
            
            # Проверяем, есть ли уже такой заказ
            existing_order = next((o for o in orders if o["user_id"] == user_id), None)
            if existing_order:
                existing_order["form_data"] = message.text
            else:
                orders.append(order_details)
            
            await message.answer("Анкета получена. Теперь отправьте скриншот оплаты.")
        
        elif message.photo:
            # Это скриншот
            existing_order = next((o for o in orders if o["user_id"] == user_id), None)
            if existing_order:
                existing_order["payment_screenshot"] = message.photo[-1].file_id
                
                # Отправляем уведомление владельцу
                admin_message = f"Новый заказ от @{message.from_user.username}:\n\n"
                admin_message += f"Товары:\n" + "\n".join(f"• {item}" for item in user_cart[user_id]) + "\n\n"
                admin_message += f"Анкета:\n{existing_order['form_data']}\n\n"
                admin_message += "Скриншот оплаты прикреплен."
                
                await bot.send_photo('@whyresale', existing_order["payment_screenshot"], caption=admin_message)
                
                await message.answer("Спасибо за заказ! Мы обработаем его в ближайшее время.")
                user_cart[user_id] = []  # Очищаем корзину
            else:
                await message.answer("Пожалуйста, сначала отправьте заполненную анкету.")
    else:
        await message.answer("Ваша корзина пуста. Невозможно обработать заказ.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
