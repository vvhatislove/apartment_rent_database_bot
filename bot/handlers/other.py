from telebot import TeleBot
from telebot.types import Message

from bot.buttons import NameOfButton
from bot.handlers.utils import USER_START_MENU
from bot.keyboard.reply.main import ReplyKeyboard


def cancel_command(message: Message, bot: TeleBot):
    keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
    bot.send_message(message.chat.id, 'Действие отменено!', reply_markup=keyboard)


def register_other_handlers(bot) -> None:
    bot.register_message_handler(cancel_command,
                                 func=lambda message: message.text == NameOfButton.CANCEL,
                                 pass_bot=True)
