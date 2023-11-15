from telebot import TeleBot
from telebot.types import Message


# def state_cancel_command(message: Message, bot: TeleBot):
#     bot.send_message(message.chat.id, 'Действие отменено!')
#     bot.delete_state(message.from_user.id, message.chat.id)


def register_other_handlers(bot) -> None:
    pass
    # bot.register_message_handler(state_cancel_command, state='*', commands='cancel', pass_bot=True)
