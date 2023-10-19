from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.buttons import NameOfButton
from bot.handlers.utils import get_user_existing_or_admin
from bot.keyboard.reply.main import ReplyKeyboard


async def user_start_command(message: Message, bot: AsyncTeleBot):
    user = await get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.ADD_NEW_ENTRY,
                                                NameOfButton.DELETE_ENTRY,
                                                NameOfButton.EDIT_ENTRY,
                                                NameOfButton.FIND_ENTRY,
                                                NameOfButton.UPLOAD_TO_EXCEL)

    await bot.send_message(message.chat.id, f'Привет пользователь {user.name}', reply_markup=keyboard)


def register_user_handlers(bot):
    bot.register_message_handler(user_start_command,
                                 commands=['user_start'],
                                 pass_bot=True)
