import os
import asyncio
import aiosqlite

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


class Booking(StatesGroup):
    service = State()
    name = State()
    phone = State()


menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📅 Записаться")],
        [KeyboardButton(text="ℹ️ О нас")]
    ],
    resize_keyboard=True
)


async def init_db():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            name TEXT,
            phone TEXT
        )
        """)
        await db.commit()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Добро пожаловать!\nВыберите действие:",
        reply_markup=menu
    )


@dp.message(F.text == "ℹ️ О нас")
async def about(message: Message):
    await message.answer(
        "Тестовый бот записи клиентов."
    )


@dp.message(F.text == "📅 Записаться")
async def booking_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите услугу:\n\nНапример:\nСтрижка\nМаникюр\nКонсультация"
    )
    await state.set_state(Booking.service)


@dp.message(Booking.service)
async def get_service(message: Message, state: FSMContext):
    await state.update_data(service=message.text)
    await message.answer("Введите ваше имя:")
    await state.set_state(Booking.name)


@dp.message(Booking.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(Booking.phone)


@dp.message(Booking.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)

    data = await state.get_data()

    async with aiosqlite.connect("database.db") as db:
        await db.execute(
            """
            INSERT INTO bookings(service, name, phone)
            VALUES (?, ?, ?)
            """,
            (
                data["service"],
                data["name"],
                data["phone"]
            )
        )
        await db.commit()

    text = (
        "Новая запись!\n\n"
        f"Услуга: {data['service']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}"
    )

    await bot.send_message(ADMIN_ID, text)

    await message.answer(
        "✅ Заявка успешно отправлена."
    )

    await state.clear()


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
