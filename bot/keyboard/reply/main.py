from telebot import types


class ReplyKeyboard:

    @staticmethod
    def get_reply_keyboard(*args):
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for arg in args:
            keyboard.add(types.KeyboardButton(arg))
        return keyboard
