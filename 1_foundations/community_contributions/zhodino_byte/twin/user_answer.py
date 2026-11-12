from aiogram import Bot, Dispatcher, types

from config import TELEGRAM_CHAT_ID
from human_bridge import resolve_question

dp = Dispatcher()
bot: Bot | None = None


def create_bot(token: str) -> Bot:
    """Create the shared Telegram bot after configuration is validated."""
    global bot
    bot = Bot(token=token)
    return bot


def get_bot() -> Bot:
    if bot is None:
        raise RuntimeError("Telegram bot has not been initialized")
    return bot


@dp.message()
async def echo_handler(message: types.Message):
    if str(message.chat.id) != TELEGRAM_CHAT_ID:
        return

    replied_message = message.reply_to_message
    if replied_message is None:
        await message.answer(
            "Чтобы ответить посетителю сайта, используйте Reply на сообщении с вопросом."
        )
        return

    answer = message.text or message.caption
    if not answer:
        await message.answer("Пожалуйста, отправьте текстовый ответ.")
        return

    if resolve_question(replied_message.message_id, answer):
        await message.answer("Ответ передан агенту и будет показан посетителю.")
    else:
        await message.answer(
            "Вопрос уже закрыт или время ожидания ответа закончилось."
        )
