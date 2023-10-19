from telebot.asyncio_handler_backends import State, StatesGroup


class AdminState(StatesGroup):
    add_new_user = State()
    delete_user = State()
