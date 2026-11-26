import asyncio
import os

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


async def send_telegram_message(message: str) -> None:
    async with Bot(token=TELEGRAM_BOT_TOKEN) as bot:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


@dp.message()
async def message_handler(message: types.Message):
    replied_message = message.reply_to_message
    if not replied_message:
        await message.answer("You need to reply to bot message")
        return

    if replied_message.from_user and replied_message.from_user.id == bot.id:
        await message.answer("This is bot message")
    else:
        await message.answer("This is not bot message")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
