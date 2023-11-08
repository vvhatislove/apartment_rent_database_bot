from telebot.asyncio_handler_backends import State, StatesGroup


class AdminState(StatesGroup):
    add_new_user = State()
    delete_user = State()


class AddNewLeaseState(StatesGroup):
    add_client_number = State()
    add_or_choose_existing_apartment = State()
    get_client_name = State()
    get_document_photos = State()
    add_apartment_address = State()
