import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import os

BOT_TOKEN = "7346291411:AAEySV35XOFkd35q_7JIIj1Fe7GzE12SNA4"
API_TOKEN = os.getenv('BOT_TOKEN')
PORT = int(os.environ.get("PORT", 10000))  # Порт для Render

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

user_carts = {}

catalog = {
    "Верхняя одежда": [],
    "Футболки/Майки/Топы": [],
    "Штаны/Брюки/Шорты": [
        {
            "name": "Джинсы Balenciaga",
            "price": "7990₽",
            "sizes": "S-XL",
            "photo": "https://example.com/photo1.jpg"
        },
        {
            "name": "Спортивные брюки Balenciaga, черные, двойная талия",
            "price": "9990₽",
            "sizes": "S-XL",
            "photo": "https://example.com/photo2.jpg"
        },
        {
            "name": "Спортивные брюки Balenciaga, серые, двойная талия",
            "price": "9990₽",
            "sizes": "S-XL",
            "photo": "https://example.com/photo3.jpg"
        },
        {
            "name": "Джинсовые брюки Vuja De Diviser (наизнанку)",
            "price": "10990₽",
            "sizes": "S-XL",
            "photo": "https://example.com/photo4.jpg"
        },
    ],
    "Худи/Свитеры": [],
    "Обувь": [
        {
            "name": "New Balance 2002R",
            "price": "6000₽",
            "sizes": "36-45 EU",
            "photo": "https://example.com/n1.jpg"
        },
        {
            "name": "Dior B22",
            "price": "9900₽",
            "sizes": "36-45 EU",
            "photo": "https://example.com/n2.jpg"
        },
        {
            "name": "Dior B23",
            "price": "14900₽",
            "sizes": "36-45 EU",
            "photo": "https://example.com/n3.jpg"
        },
        {
            "name": "Prada Cloudbust Thunder",
            "price": "16900₽",
            "sizes": "36-45 EU",
            "photo": "https://example.com/n4.jpg"
        },
        {
            "name": "Yeezy Boost 350 (разные расцветки)",
            "price": "6190₽",
            "sizes": "36-45 EU",
            "photo": "https://example.com/n5.jpg"
        }
    ],
    "Аксессуары": []
}


class OrderForm(StatesGroup):
    full_name = State()
    address = State()
    phone = State()
    payment = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Каталог", callback_data="catalog"))
    keyboard.add(InlineKeyboardButton("Отзывы", callback_data="reviews"))
    keyboard.add(InlineKeyboardButton("О нас", callback_data="about"))
    await message.answer("Привет! Добро пожаловать в why resale.", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'catalog')
async def catalog_menu(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    for category in catalog.keys():
        keyboard.add(InlineKeyboardButton(category, callback_data=f"category:{category}"))
    keyboard.add(InlineKeyboardButton("Назад", callback_data="back_to_main"))
    await bot.send_message(callback_query.from_user.id, "Выберите категорию:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('category:'))
async def show_category(callback_query: types.CallbackQuery):
    category_name = callback_query.data.split(':')[1]
    items = catalog.get(category_name, [])
    if not items:
        await bot.send_message(callback_query.from_user.id, "В этой категории пока нет товаров.")
    else:
        for item in items:
            keyboard = InlineKeyboardMarkup()
            keyboard.add(InlineKeyboardButton("Добавить в корзину", callback_data=f"add_to_cart:{item['name']}"))
            await bot.send_photo(callback_query.from_user.id, item["photo"],
                                 caption=f"{item['name']}\nРазмеры: {item['sizes']}\nЦена: {item['price']}",
                                 reply_markup=keyboard)
    back = InlineKeyboardMarkup().add(InlineKeyboardButton("Назад", callback_data="catalog"))
    await bot.send_message(callback_query.from_user.id, "⬅ Назад", reply_markup=back)


@dp.callback_query_handler(lambda c: c.data.startswith('add_to_cart:'))
async def add_to_cart(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    product_name = callback_query.data.split(':')[1]
    user_carts.setdefault(user_id, []).append(product_name)
    await bot.answer_callback_query(callback_query.id, text=f"Товар «{product_name}» добавлен в корзину.")


@dp.message_handler(commands=['cart'])
async def view_cart(message: types.Message):
    user_id = message.from_user.id
    cart = user_carts.get(user_id, [])
    if not cart:
        await message.answer("Ваша корзина пуста.")
        return

    text = "🛒 Ваша корзина:\n" + "\n".join([f"- {item}" for item in cart])
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Оформить заказ", callback_data="checkout"))
    keyboard.add(InlineKeyboardButton("Очистить корзину", callback_data="clear_cart"))
    await message.answer(text, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "checkout")
async def checkout(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Оформить заказ", callback_data="start_order"))
    await bot.send_message(callback_query.from_user.id, "Вы готовы оформить заказ?", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == "start_order")
async def start_order(callback_query: types.CallbackQuery):
    await OrderForm.full_name.set()
    await bot.send_message(callback_query.from_user.id, "Пожалуйста, введите ваше ФИО:")


@dp.message_handler(state=OrderForm.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await OrderForm.next()
    await message.answer("Введите адрес доставки:")


@dp.message_handler(state=OrderForm.address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await OrderForm.next()
    await message.answer("Введите номер телефона:")


@dp.message_handler(state=OrderForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await OrderForm.next()
    await message.answer("Отправьте скриншот с подтверждением оплаты.")


@dp.message_handler(state=OrderForm.payment, content_types=types.ContentType.PHOTO)
async def process_payment(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    full_name = user_data.get('full_name')
    address = user_data.get('address')
    phone = user_data.get('phone')
    payment_screenshot = message.photo[-1].file_id

    # Сообщение админу
    admin_id = "@whyresale"
    await bot.send_message(admin_id, f"Новый заказ:\nФИО: {full_name}\nАдрес: {address}\nТелефон: {phone}\nСкриншот оплаты: {payment_screenshot}")

    # Закрытие формы
    await state.finish()

    await message.answer("Ваш заказ оформлен! Мы свяжемся с вами для подтверждения.")
    await bot.send_message(message.chat.id, "Спасибо за покупку!")
