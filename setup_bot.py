import schedule
import threading
import time

from telebot import TeleBot

from bot.handlers import register_all_handlers
from bot.misc.main import beep
from misc.env import EnvironmentVariable


def __on_start_up(bot) -> None:
    register_all_handlers(bot)


def start_bot():
    bot_token = EnvironmentVariable.BOT_TOKEN
    bot = TeleBot(bot_token)
    schedule.every(5).seconds.do(beep, 474625366, bot).tag(474625366)
    __on_start_up(bot)
    bot.polling()
    # threading.Thread(target=bot.infinity_polling, name='bot_infinity_polling', daemon=True).start()
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
