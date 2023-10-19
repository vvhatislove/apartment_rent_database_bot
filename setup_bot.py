from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
import asyncio

from bot.handlers import register_all_handlers
from misc.env import EnvironmentVariable


def __on_start_up(bot) -> None:
    register_all_handlers(bot)


def start_bot():
    bot_token = EnvironmentVariable.BOT_TOKEN
    bot = AsyncTeleBot(bot_token)
    bot.add_custom_filter(asyncio_filters.StateFilter(bot))
    __on_start_up(bot)
    asyncio.run(bot.polling(restart_on_change=True, skip_pending=True))
