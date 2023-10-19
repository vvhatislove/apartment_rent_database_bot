from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message


async def state_cancel_command(message: Message, bot: AsyncTeleBot):
    await bot.send_message(message.chat.id, 'Действие отменено!')
    await bot.delete_state(message.from_user.id, message.chat.id)


def register_other_handlers(bot) -> None:
    bot.register_message_handler(state_cancel_command, state='*', commands='cancel', pass_bot=True)
