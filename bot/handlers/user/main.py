import json

from telebot import types
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from bot.buttons import NameOfButton
from bot.handlers.utils import get_user_existing_or_admin, validate_ukrainian_phone_number, \
    generate_unique_filename, check_date_format, parse_date_values, get_lease_info
from bot.keyboard.reply.main import ReplyKeyboard
from bot.states.main import AddNewLeaseState
from database import Database


def user_start_command(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.ADD_NEW_LEASE_ENTRY,
                                                NameOfButton.FIND_LEASE_ENTRY)
    # NameOfButton.DELETE_ENTRY,
    # NameOfButton.EDIT_ENTRY,

    # NameOfButton.UPLOAD_TO_EXCEL)

    bot.send_message(message.chat.id, f'👋Привет пользователь {user.name}', reply_markup=keyboard)


def add_new_lease_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    bot.send_message(message.chat.id, 'Напишите номер телефона клиента📱',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.set_state(message.from_user.id, AddNewLeaseState.add_client_number, message.chat.id)
    bot.register_next_step_handler(message, add_client_number, bot)


def add_client_number(message: Message, bot: TeleBot):
    data = {}
    phone_number = validate_ukrainian_phone_number(message.text)
    if phone_number is None:
        bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
        bot.register_next_step_handler(message, add_client_number, bot)
    else:
        db = Database()
        client = db.get_client_by_phone_number(phone_number)
        if client is None:
            bot.send_message(message.chat.id, 'В базе нет клиента, с таким номером телефона📖.\nСоздаем нового✍️.')
            bot.send_message(message.chat.id, 'Отправьте мне имя и фамилию клиента👱‍♂️')

            data['phone_number'] = phone_number
            bot.register_next_step_handler(message, get_client_name, bot, data)
        else:
            bot.send_message(message.chat.id, '⚠️Такой клиент уже добавлен в базу!\n\n'
                                              f'👱‍♂️Имя: {client.name}\n'
                                              f'📱Номер телефона: {", ".join([phone_number.number for phone_number in client.phone_numbers])}')
            ask_apartment_address(message, bot, {'client_id': client.id})


def get_client_name(message: Message, bot: TeleBot, data):
    client_name = message.text
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CONFIRM_PHOTOS_UPLOADING)
    bot.send_message(message.chat.id, 'Теперь пришлите фотографии его документов📑.\n\n'
                                      'ВАЖНО! Отправляйте каждое фото отдельным сообщением, после чего нажмите 👍',
                     reply_markup=keyboard)
    data['client_name'] = client_name
    data['path_images'] = []
    bot.set_state(message.from_user.id, AddNewLeaseState.get_document_photos, message.chat.id)
    bot.register_next_step_handler(message, get_document_photos, bot, data)


def get_document_photos(message: Message, bot: TeleBot, data):
    if message.content_type == 'photo':
        path_image = f'doc_images/{generate_unique_filename()}.jpg'
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(path_image, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(message.chat.id, 'Изображение загружено✅')
        data['path_images'].append(path_image)
        bot.register_next_step_handler(message, get_document_photos, bot, data)
    elif message.content_type == 'text':
        if message.text == '👍':
            add_client_into_db(message, bot, data)


def add_client_into_db(message: Message, bot: TeleBot, data):
    client_name = data.get('client_name')
    phone_number = data.get('phone_number')
    path_images = data.get('path_images')
    db = Database()
    client_id = db.add_client(client_name, [phone_number], path_images)
    bot.send_message(message.chat.id, '🆕Новый клиент\n\n'
                                      f'👱‍♂️Имя: {client_name}\n'
                                      f'📱Номер телефона: {phone_number}\n'
                                      f'📑Кол-во загруженных фото: {len(path_images)}\n\n'
                                      '✅Успешно добавлен', reply_markup=types.ReplyKeyboardRemove())
    data = {'client_id': client_id}
    ask_apartment_address(message, bot, data)


def ask_apartment_address(message: Message, bot: TeleBot, data):
    db = Database()
    apartments = db.get_all_apartments()
    markup = types.InlineKeyboardMarkup()
    for apartment in apartments:
        data_ = data.copy()
        data_['apartment_id'] = apartment.id
        markup.add(types.InlineKeyboardButton(apartment.address, callback_data=json.dumps(data_)))
    markup.add(types.InlineKeyboardButton('🆕Добавить и выбрать новый адрес', callback_data=json.dumps(data)))
    f = bot.send_message(message.chat.id, '🤔Выберете адрес или создайте новый.', reply_markup=markup)


def apartment_callback(callback: CallbackQuery, bot: TeleBot):
    if callback.message:
        data = json.loads(callback.data)
        if data.get('apartment_id'):
            bot.edit_message_text('🗓Теперь отправьте мне с период сдачи квартиры.\n\n'
                                  '⚠️Формат сообщения: "ДД.MM.ГГГГ:ЧЧ.ММ-ДД.MM.ГГГГ:ЧЧ.ММ"\n'
                                  'Например: 26.11.2023:12.00-26.01.2024:13.00',
                                  callback.message.chat.id,
                                  callback.message.message_id, reply_markup=None)
            bot.register_next_step_handler(callback.message, get_rent_period, bot, data)
        else:
            bot.edit_message_text('🏠Напишите адрес квартиры', callback.message.chat.id, callback.message.message_id,
                                  reply_markup=None)
            bot.register_next_step_handler(callback.message, get_new_apartment_address, bot, data)


def get_new_apartment_address(message: Message, bot: TeleBot, data):
    apartment_address = message.text
    db = Database()
    apartment_id = db.add_apartment(apartment_address)
    bot.send_message(message.chat.id, '✅Квартира по новому адресу успешно добавлена!')
    bot.send_message(message.chat.id, '🗓Теперь отправьте мне с период сдачи квартиры.\n\n'
                                      '⚠️Формат сообщения: "ДД.MM.ГГГГ:ЧЧ.ММ-ДД.MM.ГГГГ:ЧЧ.ММ"\n'
                                      'Например: 26.11.2023:12.00-26.01.2024:13.00')
    data['apartment_id'] = apartment_id
    bot.register_next_step_handler(message, get_rent_period, bot, data)


def get_rent_period(message: Message, bot: TeleBot, data: dict):
    if not check_date_format(message.text):
        bot.send_message(message.chat.id, '❌Не правильный формат.\n\n'
                                          '⚠️Формат сообщения должен быть: "ДД.MM.ГГГГ:ЧЧ.ММ-ДД.MM.ГГГГ:ЧЧ.ММ"')
        bot.register_next_step_handler(message, get_rent_period, bot, data)
    else:
        start_date, end_date = parse_date_values(message.text)
        data['start_date'] = start_date
        data['end_date'] = end_date
        bot.send_message(message.chat.id, '💵Теперь отправьте мне сумму арендной платы')
        bot.register_next_step_handler(message, get_rent_amount, bot, data)


def get_rent_amount(message: Message, bot: TeleBot, data: dict):
    if not message.text.isdigit() or not message.text.isdecimal():
        bot.send_message(message.chat.id, '❌Это не числовое значение.\n'
                                          '⚠️Отправьте корректное число.')
        bot.register_next_step_handler(message, get_rent_period, bot, data)
    else:
        data['rent_amount'] = float(message.text)
        bot.send_message(message.chat.id, '💸Теперь отправьте мне сумму залога')
        bot.register_next_step_handler(message, get_deposit, bot, data)


def get_deposit(message: Message, bot: TeleBot, data: dict):
    if not message.text.isdigit() or not message.text.isdecimal():
        bot.send_message(message.chat.id, '❌Это не числовое значение.\n'
                                          '⚠️Отправьте корректное число.')
        bot.register_next_step_handler(message, get_deposit, bot, data)
    else:
        data['deposit'] = float(message.text)
        bot.send_message(message.chat.id, '✍️Теперь можете оставить дополнительные комментарии\n\n'
                                          '⚠️Если комментарий не нужен отправьте цифру 0')
        bot.register_next_step_handler(message, get_additional_details, bot, data)


def get_additional_details(message: Message, bot: TeleBot, data: dict):
    if message.text.isdigit():
        if int(message.text) == 0:
            data['additional_details'] = ''
            bot.send_message(message.chat.id, '💨Комментарий пропущен')
    else:
        data['additional_details'] = message.text
        bot.send_message(message.chat.id, '✅Комментарий был добавлен')
    add_new_lease_into_db(message, bot, data)


def add_new_lease_into_db(message: Message, bot: TeleBot, data: dict):
    db = Database()
    client_id = data.get('client_id')
    apartment_id = data.get('apartment_id')
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    rent_amount = data.get('rent_amount')
    deposit = data.get('deposit')
    additional_details = data.get('additional_details')
    lease_id = db.add_lease(client_id, apartment_id, start_date, end_date, rent_amount, deposit, additional_details)
    lease = db.get_lease_by_id(lease_id)
    lease_info_message = get_lease_info(lease)
    bot.send_message(message.chat.id, '✅Запись об аренде успешно добавлена!\n\n' + lease_info_message)


def find_lease_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.FIND_LEASE_BY_PHONE_NUMBER,
                                                NameOfButton.FIND_LEASE_BY_DATE)
    bot.send_message(message.chat.id, 'Выберите по какому параметру будем искать записи', reply_markup=keyboard)


def find_lease_by_phone_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    bot.send_message(message.chat.id, 'Отправьте мне номер телефона с которым нужно искать записи аренд',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_phone_number_for_search, bot)


def get_phone_number_for_search(message: Message, bot: TeleBot):
    phone_number = validate_ukrainian_phone_number(message.text)
    if phone_number:
        db = Database()
        leases = db.search_leases(phone_number=phone_number)
        if leases:
            message_info_leases = '\n\n'.join(get_lease_info(lease) for lease in leases)
            bot.send_message(message.chat.id, 'Найдены такие совпадения:\n\n' + message_info_leases)
        else:
            bot.send_message(message.chat.id, 'Совпадений не найдено')
    else:
        bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
        bot.register_next_step_handler(message, get_phone_number_for_search, bot)


def register_user_handlers(bot):
    bot.register_message_handler(user_start_command,
                                 commands=['user_start'],
                                 pass_bot=True)

    bot.register_message_handler(add_new_lease_button,
                                 func=lambda message: message.text == NameOfButton.ADD_NEW_LEASE_ENTRY,
                                 pass_bot=True)
    bot.register_message_handler(find_lease_button,
                                 func=lambda message: message.text == NameOfButton.FIND_LEASE_ENTRY,
                                 pass_bot=True)
    bot.register_message_handler(find_lease_by_phone_button,
                                 func=lambda message: message.text == NameOfButton.FIND_LEASE_BY_PHONE_NUMBER,
                                 pass_bot=True)


def register_user_callback_handlers(bot):
    bot.register_callback_query_handler(apartment_callback,
                                        func=lambda call: True,
                                        pass_bot=True)
