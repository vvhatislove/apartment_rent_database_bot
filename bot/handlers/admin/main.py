from telebot import types
from telebot import TeleBot
from telebot.types import Message

from bot.buttons import NameOfButton
from bot.handlers.utils import get_user_existing_or_admin
from bot.keyboard.reply.main import ReplyKeyboard
from bot.states import AdminState
from database import Database


def admin_start_command(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot, check_admin=True)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.ADD_NEW_USER, NameOfButton.DELETE_USER)
    bot.send_message(message.chat.id, f'Привет, админ {user.name}', reply_markup=keyboard)


def add_new_user_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot, check_admin=True)
    if user is None:
        return
    bot.send_message(message.chat.id,
                     'Перешлите любое сообщение от пользователя, которого хотите добавить в систему\n'
                     '[/cancel - для отмены действия]',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_new_user_data, bot)


def get_new_user_data(message: Message, bot: TeleBot):
    print(message)
    # todo доделать регистрацию пользователей, сделать ручной ввод id
    if message.forward_sender_name is None and message.forward_from is None:
        bot.send_message(message.chat.id, 'Это не пересланное сообщение!')
    else:
        if message.forward_from.id == message.from_user.id:
            bot.send_message(message.chat.id, 'Это сообщение принадлежит вам же!')
        else:
            if message.forward_from.first_name is None and message.forward_from.last_name is None:
                name = message.forward_from.username
            else:
                name = ' '.join([message.forward_from.first_name, message.forward_from.last_name])
            tg_user_id = message.forward_from.id
            is_admin = False
            db = Database()
            db.create_user_if_not_exist(name, tg_user_id, is_admin)
            bot.send_message(message.chat.id, 'Новый пользователь добавлен в систему.\n'
                                              f'Имя: {name}\n'
                                              f'Telegram ID: {tg_user_id}')


def delete_user_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot, check_admin=True)
    if user is None:
        return
    db = Database()
    users = db.get_all_users()
    bot.send_message(message.chat.id, 'Отправьте Telegram ID пользователя, которого нужно удалить из системы.\n'
                                      '[/cancel - для отмены действия]', reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, 'Список пользователей:')
    str_for_answer = '\n\n'.join(
        [f'Имя: {user.name}\nTelegram ID: {user.tg_user_id}' for user in users if not user.is_admin])
    bot.send_message(message.chat.id, str_for_answer)
    bot.register_next_step_handler(message, get_tg_id_for_deleting, bot, users)


def get_tg_id_for_deleting(message: Message, bot: TeleBot, users):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, 'Это не похоже на ID. Это не число!')
    else:
        tg_user_id = int(message.text)
        for user in users:
            if tg_user_id == user.tg_user_id:
                db = Database()
                db.delete_user_by_id(user.id)
                bot.send_message(message.chat.id, f'Пользователь {user.name} успешно удален!')
                break
        else:
            bot.send_message(message.chat.id, 'Нет пользователя с таким Telegram ID!')


def register_admin_handlers(bot) -> None:
    bot.register_message_handler(admin_start_command,
                                 commands=['admin_start'],
                                 pass_bot=True)
    bot.register_message_handler(add_new_user_button,
                                 func=lambda message: message.text == NameOfButton.ADD_NEW_USER,
                                 pass_bot=True)

    bot.register_message_handler(delete_user_button,
                                 func=lambda message: message.text == NameOfButton.DELETE_USER,
                                 pass_bot=True)
