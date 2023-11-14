from telebot import custom_filters
from telebot import TeleBot

from bot.handlers import register_all_handlers
from misc.env import EnvironmentVariable


def __on_start_up(bot) -> None:
    register_all_handlers(bot)


def start_bot():
    bot_token = EnvironmentVariable.BOT_TOKEN
    bot = TeleBot(bot_token)
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    __on_start_up(bot)
    bot.polling()
