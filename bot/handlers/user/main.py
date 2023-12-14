import json
from datetime import datetime

from telebot import types, ContinueHandling
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from bot.buttons import NameOfButton
from bot.handlers.utils import get_user_existing_or_admin, validate_ukrainian_phone_number, \
    generate_unique_filename, check_date_format, parse_date_values, get_lease_info, USER_START_MENU
from bot.keyboard.reply.main import ReplyKeyboard
from bot.states.main import AddNewLeaseState
from database import Database


def user_start_command(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)

    bot.send_message(message.chat.id, f'👋Привет пользователь {user.name}', reply_markup=keyboard)


def add_new_lease_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
    bot.send_message(message.chat.id, 'Напишите номер телефона клиента📱',
                     reply_markup=keyboard)
    bot.set_state(message.from_user.id, AddNewLeaseState.add_client_number, message.chat.id)
    bot.register_next_step_handler(message, add_client_number, bot)


def add_client_number(message: Message, bot: TeleBot):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
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
            # bot.send_message(message.chat.id, 'Отправьте мне имя и фамилию клиента👱‍♂️')

            data['phone_number'] = phone_number
            add_client_into_db(message, bot, data)
            # bot.register_next_step_handler(message, get_client_name, bot, data)
        else:
            bl_entry = db.get_blacklist_entry(client.id)
            if bl_entry:
                keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
                bot.send_message(message.chat.id,
                                 '⛔⛔⛔Клиент в черном списке!\n\n'
                                 f'👱‍♂️Имя: {client.name if client.name else "Не известно"}\n'
                                 f'📱Номер телефона: {", ".join([phone_number.number for phone_number in client.phone_numbers])}\n'
                                 f'Комментарий ЧС: {bl_entry.comment}',
                                 reply_markup=keyboard)
            else:
                bot.send_message(message.chat.id,
                                 '⚠️С таким номером уже есть запись о клиенте!\n\n'
                                 f'👱‍♂️Имя: {client.name if client.name else "Не известно"}\n'
                                 f'📱Номер телефона: {", ".join([phone_number.number for phone_number in client.phone_numbers])}',
                                 reply_markup=types.ReplyKeyboardRemove())
                ask_apartment_address(message, bot, {'client_id': client.id})


def add_client_into_db(message: Message, bot: TeleBot, data):
    client_name = data.get('client_name')
    client_name = client_name if client_name else ''
    phone_number = data.get('phone_number')
    path_images = data.get('path_images')
    path_images = path_images if path_images else []
    db = Database()
    client_id = db.add_client(client_name, [phone_number], path_images)
    bot.send_message(message.chat.id, '🆕Новый клиент\n\n'
                                      f'👱‍♂️Имя: {client_name if client_name else "Не известно"}\n'
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
    markup.add(types.InlineKeyboardButton('Отмена', callback_data=NameOfButton.CANCEL))
    bot.send_message(message.chat.id, '🤔Выберете адрес или создайте новый.', reply_markup=markup)


def apartment_callback(callback: CallbackQuery, bot: TeleBot):
    if callback.message:
        if callback.data == NameOfButton.CANCEL:
            bot.edit_message_text('Отменено',
                                  callback.message.chat.id,
                                  callback.message.message_id, reply_markup=None)
            keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
            bot.send_message(callback.message.chat.id, 'Выберите другой пункт меню', reply_markup=keyboard)
            return
        data = json.loads(callback.data)
        keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
        if data.get('apartment_id'):
            bot.edit_message_text('🗓Теперь отправьте мне начало периода сдачи квартиры.\n\n'
                                  '⚠️Формат сообщения: "ДД.MM/ЧЧ.ММ"\n'
                                  'Или если вы хотите указать год в ручную, то формат должен быть:\n'
                                  '"ДД.MM.ГГГГ/ЧЧ.ММ"',
                                  callback.message.chat.id,
                                  callback.message.message_id, reply_markup=None)
            bot.send_message(callback.message.chat.id,
                             'Например: 26.11/12:00 или 26.11.2023/12:00',
                             reply_markup=keyboard)
            bot.register_next_step_handler(callback.message, get_rent_period_start, bot, data)
        elif data.get('callback'):
            return ContinueHandling()
        else:
            bot.edit_message_text('🏠Напишите адрес квартиры', callback.message.chat.id, callback.message.message_id,
                                  reply_markup=None)
            bot.send_message(callback.message.chat.id, 'которую хотите добавить.', reply_markup=keyboard)
            bot.register_next_step_handler(callback.message, get_new_apartment_address, bot, data)


def get_new_apartment_address(message: Message, bot: TeleBot, data):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    apartment_address = message.text
    db = Database()
    apartment_id = db.add_apartment(apartment_address)
    bot.send_message(message.chat.id, '✅Квартира по новому адресу успешно добавлена!')
    bot.send_message(message.chat.id, '🗓Теперь отправьте мне начало периода сдачи квартиры.\n\n'
                                      '⚠️Формат сообщения: "ДД.MM/ЧЧ.ММ"\n'
                                      'Или если вы хотите указать год в ручную, то формат должен быть:\n'
                                      '"ДД.MM.ГГГГ/ЧЧ.ММ"\n\n'
                                      'Например: 26.11/12:00 или 26.11.2023/12:00')
    data['apartment_id'] = apartment_id
    bot.register_next_step_handler(message, get_rent_period_start, bot, data)


def get_rent_period_start(message: Message, bot: TeleBot, data: dict):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    start_date = check_date_format(message.text)
    if start_date is None:
        bot.send_message(message.chat.id, '❌Не правильный формат.\n\n'
                                          '⚠️Формат сообщения должен быть: "ДД.MM/ЧЧ.ММ"\n\n'
                                          'Или если вы хотите указать год в ручную, то формат должен быть:\n'
                                          '"ДД.MM.ГГГГ/ЧЧ.ММ"')
        bot.register_next_step_handler(message, get_rent_period_start, bot, data)
    else:
        data['start_date'] = start_date
        bot.send_message(message.chat.id, 'Хорошо, теперь отправьте мне конец периода сдачи')
        bot.register_next_step_handler(message, get_rent_period_end, bot, data)


def get_rent_period_end(message: Message, bot: TeleBot, data: dict):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    end_date = check_date_format(message.text)
    if end_date is None:
        bot.send_message(message.chat.id, '❌Не правильный формат.\n\n'
                                          '⚠️Формат сообщения должен быть: "ДД.MM/ЧЧ.ММ"\n\n'
                                          'Или если вы хотите указать год в ручную, то формат должен быть:\n'
                                          '"ДД.MM.ГГГГ/ЧЧ.ММ"')
        bot.register_next_step_handler(message, get_rent_period_end, bot, data)

    else:
        if data.get('start_date') > end_date:
            bot.send_message(message.chat.id, 'Дата начала аренды больше чем конечная!\n'
                                              'Введите корректное значение конечной даты')
            bot.register_next_step_handler(message, get_rent_period_end, bot, data)
        db = Database()
        overlapping_lease_id = db.get_lease_id_by_date_time_range(data.get('apartment_id'),
                                                                  data.get('start_date'),
                                                                  end_date)
        if overlapping_lease_id is None:
            data['end_date'] = end_date
            keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.NO_DEPOSIT, NameOfButton.CANCEL)
            bot.send_message(message.chat.id, '💵Теперь отправьте мне сумму залога\n\n'
                                              'Если залог не требуется напишите 0, либо нажмите соответствующую кнопку',
                             reply_markup=keyboard)
            bot.register_next_step_handler(message, get_deposit, bot, data)
        else:
            overlapping_lease = db.get_lease_by_id(overlapping_lease_id)
            bot.send_message(message.chat.id, 'Найдено пересечение дат с уже существующей бронью!')
            bot.send_message(message.chat.id, get_lease_info(overlapping_lease))
            bot.send_message(message.chat.id, 'Пожалуйста, введите заново дату начала аренды')
            bot.register_next_step_handler(message, get_rent_period_start, bot, data)


def get_deposit(message: Message, bot: TeleBot, data: dict):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    elif message.text == NameOfButton.NO_DEPOSIT or message.text == '0':
        keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
        bot.send_message(message.chat.id, 'Залог для этой брони не требуется\n\n', reply_markup=keyboard)
        bot.send_message(message.chat.id, '💸Теперь отправьте мне сумму арендной платы')
        data['deposit'] = 0.0
        bot.register_next_step_handler(message, get_rent_amount, bot, data)
    elif not message.text.isdigit() or not message.text.isdecimal():
        bot.send_message(message.chat.id, '❌Это не числовое значение.\n'
                                          '⚠️Отправьте корректное число.')
        bot.register_next_step_handler(message, get_rent_period_start, bot, data)
    else:
        data['deposit'] = float(message.text)
        keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
        bot.send_message(message.chat.id, '⚠️Внимание! Бронирование удалится через сутки '
                                          'с момента сохранения, если вы не подтвердите его внесение '
                                          'в соответствующем пункте меню', reply_markup=keyboard)
        bot.send_message(message.chat.id, '💸Теперь отправьте мне сумму арендной платы')
        bot.register_next_step_handler(message, get_rent_amount, bot, data)


def get_rent_amount(message: Message, bot: TeleBot, data: dict):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    if not message.text.isdigit() or not message.text.isdecimal():
        bot.send_message(message.chat.id, '❌Это не числовое значение.\n'
                                          '⚠️Отправьте корректное число.')
        bot.register_next_step_handler(message, get_deposit, bot, data)
    else:
        data['rent_amount'] = float(message.text)
        bot.send_message(message.chat.id, '✍️Теперь можете оставить дополнительные комментарии\n\n'
                                          '⚠️Если комментарий не нужен отправьте цифру 0')
        bot.register_next_step_handler(message, get_additional_details, bot, data)


def get_additional_details(message: Message, bot: TeleBot, data: dict):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
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
    lease_id = db.add_lease(client_id, apartment_id, start_date, end_date, rent_amount, deposit, additional_details,
                            False)
    lease = db.get_lease_by_id(lease_id)
    lease_info_message = get_lease_info(lease)
    keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
    bot.send_message(message.chat.id, '✅Запись об аренде успешно добавлена!\n\n' + lease_info_message,
                     reply_markup=keyboard)


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
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    bot.send_message(message.chat.id, 'Отправьте мне номер телефона с которым нужно искать записи аренд',
                     reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, get_phone_number_for_search, bot)


def get_phone_number_for_search(message: Message, bot: TeleBot):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
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


def make_deposit_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
    bot.send_message(message.chat.id, 'Для пометки о внесении залога\n'
                                      'Напишите номер телефона на который забронирована квартира',
                     reply_markup=keyboard)
    bot.register_next_step_handler(message, get_phone_number_for_make_deposit, bot)


def get_phone_number_for_make_deposit(message: Message, bot: TeleBot):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    phone_number = validate_ukrainian_phone_number(message.text)
    if phone_number is None:
        bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
        bot.register_next_step_handler(message, get_phone_number_for_make_deposit, bot)
    else:
        db = Database()
        leases = db.search_leases(phone_number=phone_number,
                                  start_date=datetime.utcnow(),
                                  is_deposit_paid=False)
        for lease in leases:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton('✅Залог внесен', callback_data=json.dumps(
                {'lease_id': lease.id, 'callback': 'is_deposit_paid'})))
            bot.send_message(message.chat.id, get_lease_info(lease), reply_markup=markup)
        if not leases:
            keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
            bot.send_message(message.chat.id,
                             'Бронирований, требующих пометки о внесении залога, не найдено по данному номеру телефона',
                             reply_markup=keyboard)


def is_deposit_paid_callback(callback: CallbackQuery, bot: TeleBot):
    if callback.message:
        data = json.loads(callback.data)
        if data.get('callback') != 'is_deposit_paid':
            return ContinueHandling()
        lease_id = data.get('lease_id')
        if lease_id:
            db = Database()
            db.update_lease(lease_id, is_deposit_paid=True)
            bot.edit_message_text('Пометка о внесении залога добавлена.',
                                  callback.message.chat.id,
                                  callback.message.message_id, reply_markup=None)
            keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
            bot.send_message(callback.message.chat.id, 'Теперь бронирование не будет удалено.', reply_markup=keyboard)


def check_in_button(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    db = Database()
    available_leases = db.get_available_leases_today()
    available_leases = [lease for lease in available_leases if lease.is_inhabited == False]
    if available_leases:
        bot.send_message(message.chat.id,
                         'Выберите бронирование в котором будет происходить заселение',
                         reply_markup=types.ReplyKeyboardRemove())
    for lease in available_leases:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton('Заселение',
                                       callback_data=json.dumps({'lease_id': lease.id, 'callback': 'check_in'})))
        markup.add(types.InlineKeyboardButton('Отмена', callback_data=NameOfButton.CANCEL))
        bot.send_message(message.chat.id, get_lease_info(lease), reply_markup=markup)
    if not available_leases:
        bot.send_message(message.chat.id, 'Нет забронированных квартир на сегодняшний день')


def check_in_callback(callback: CallbackQuery, bot: TeleBot):
    if callback.message:
        data = json.loads(callback.data)
        if data.get('callback') != 'check_in':
            return ContinueHandling
        if callback.data == NameOfButton.CANCEL:
            bot.edit_message_text('Отменено',
                                  callback.message.chat.id,
                                  callback.message.message_id, reply_markup=None)
            keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
            bot.send_message(callback.message.chat.id, 'Выберите другой пункт меню', reply_markup=keyboard)
        else:
            bot.edit_message_text(callback.message.text,
                                  callback.message.chat.id,
                                  callback.message.message_id,
                                  reply_markup=None)
            db = Database()
            lease = db.get_lease_by_id(data.get('lease_id'))
            if not lease.client.name and len(lease.client.documents) == 0:
                bot.send_message(callback.message.chat.id,
                                 'У клиента не указано имя и нет фото документов.\n\n Введите имя')
                bot.register_next_step_handler(callback.message, get_client_name, bot,
                                               {'lease_id': lease.id, 'client_id': lease.client.id})
            else:
                keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CONFIRM, NameOfButton.CANCEL)
                lease = db.get_lease_by_id(data.get('lease_id'))
                bot.send_message(callback.message.chat.id, 'Данные об аренде:\n\n' + get_lease_info(lease))
                for document in lease.client.documents:
                    with open(document.filename, 'rb') as file:
                        bot.send_photo(callback.message.chat.id, file)
                bot.send_message(callback.message.chat.id, 'Подтвердить заселение?', reply_markup=keyboard)
                bot.register_next_step_handler(callback.message, check_in_note, bot, data)


def get_client_name(message: Message, bot: TeleBot, data):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    client_name = message.text
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CONFIRM_PHOTOS_UPLOADING, NameOfButton.CANCEL)
    bot.send_message(message.chat.id, 'Теперь пришлите фотографии его документов📑.\n\n'
                                      'ВАЖНО! Отправляйте каждое фото отдельным сообщением, после чего нажмите 👍',
                     reply_markup=keyboard)
    data['client_name'] = client_name
    data['path_images'] = []
    bot.set_state(message.from_user.id, AddNewLeaseState.get_document_photos, message.chat.id)
    bot.register_next_step_handler(message, get_document_photos, bot, data)


def get_document_photos(message: Message, bot: TeleBot, data):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
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
            db = Database()
            client_name = data.get('client_name')
            path_images = data.get('path_images')
            client_id = data.get('client_id')
            db.update_client(client_id, name=client_name, document_filenames=path_images)
            bot.send_message(message.chat.id, 'Данные о клиенте успешно добавлены!')
            keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CONFIRM, NameOfButton.CANCEL)
            lease = db.get_lease_by_id(data.get('lease_id'))
            bot.send_message(message.chat.id, 'Данные об аренде:\n\n' + get_lease_info(lease))
            bot.send_message(message.chat.id, 'Фото документов:')
            for document in lease.client.documents:
                with open(document.filename, 'rb') as file:
                    bot.send_photo(message.chat.id, file)
            bot.send_message(message.chat.id, 'Подтвердить заселение?', reply_markup=keyboard)
            bot.register_next_step_handler(message, check_in_note, bot, data)


def check_in_note(message: Message, bot: TeleBot, data):
    if message.text == NameOfButton.CONFIRM:
        lease_id = data.get('lease_id')
        db = Database()
        db.update_lease(lease_id, is_inhabited=True)
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Пометка о заселении успешно добавлена', reply_markup=keyboard)
    elif message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Отменено', reply_markup=keyboard)


def blacklist(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    else:
        keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.ADD_CLIENT_TO_BLACKLIST,
                                                    NameOfButton.REMOVE_CLIENT_FROM_BLACKLIST,
                                                    NameOfButton.CANCEL)
        bot.send_message(message.chat.id, 'Выберете действие', reply_markup=keyboard)


def add_or_remove_client_in_blacklist(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    elif message.text == NameOfButton.ADD_CLIENT_TO_BLACKLIST:
        keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
        bot.send_message(message.chat.id, 'Отправьте мне номер телефона клиента для добавления в ЧС',
                         reply_markup=keyboard)
        bot.register_next_step_handler(message, add_to_blacklist, bot)
    elif message.text == NameOfButton.REMOVE_CLIENT_FROM_BLACKLIST:
        keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CANCEL)
        bot.send_message(message.chat.id, 'Отправьте мне номер телефона клиента для удаления из ЧС',
                         reply_markup=keyboard)
        bot.register_next_step_handler(message, remove_from_blacklist, bot)


def add_to_blacklist(message: Message, bot: TeleBot):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    phone_number = validate_ukrainian_phone_number(message.text)
    if phone_number is None:
        bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
        bot.register_next_step_handler(message, add_to_blacklist, bot)
    else:
        db = Database()
        client = db.get_client_by_phone_number(phone_number)
        if client:
            data = {'phone_number': phone_number, 'client_id': client.id}
            bot.send_message(message.chat.id, 'Найден клиент с таким номером')
            bot.send_message(message.chat.id, 'Теперь добавьте комментарий')
            bot.register_next_step_handler(message, add_blacklist_comment, bot, data)
        else:
            bot.send_message(message.chat.id, 'Нет клиента с таким номером телефона. Попробуйте еще раз')
            bot.register_next_step_handler(message, add_to_blacklist, bot)


def add_blacklist_comment(message: Message, bot: TeleBot, data):
    comment = message.text
    phone_number = data.get('phone_number')
    client_id = data.get('client_id')
    db = Database()
    db.add_to_blacklist(client_id, comment)
    keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
    bot.send_message(message.chat.id, f'Клиент с номером {phone_number} успешно добавлен в ЧС', reply_markup=keyboard)


def remove_from_blacklist(message: Message, bot: TeleBot):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    phone_number = validate_ukrainian_phone_number(message.text)
    if phone_number is None:
        bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
        bot.register_next_step_handler(message, remove_from_blacklist, bot)
    else:
        db = Database()
        client = db.get_client_by_phone_number(phone_number)
        if not client:
            bot.send_message(message.chat.id, 'В черном списке нет клиента с таким номером. Попробуйте еще раз!')
            bot.register_next_step_handler(message, remove_from_blacklist, bot)
            return
        bl_entry = db.get_blacklist_entry(client.id)
        if bl_entry:
            db.remove_from_blacklist(client.id)
            keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
            bot.send_message(message.chat.id, 'Клиент был убран из черного списка', reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, 'В черном списке нет клиента с таким номером. Попробуйте еще раз!')
            bot.register_next_step_handler(message, remove_from_blacklist, bot)
            return


def show_client_data(message: Message, bot: TeleBot):
    user = get_user_existing_or_admin(message, bot)
    if user is None:
        return
    bot.send_message(message.chat.id, 'Отправьте номер телефона клиента')
    bot.register_next_step_handler(message, get_client_number_for_search, bot)


def get_client_number_for_search(message: Message, bot: TeleBot):
    if message.text == NameOfButton.CANCEL:
        keyboard = ReplyKeyboard.get_reply_keyboard(*USER_START_MENU)
        bot.send_message(message.chat.id, 'Действие отменено.', reply_markup=keyboard)
        return
    phone_number = validate_ukrainian_phone_number(message.text)
    if phone_number is None:
        bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
        bot.register_next_step_handler(message, get_client_number_for_search, bot)
    else:
        db = Database()
        client = db.get_client_by_phone_number(phone_number)
        if client:
            bot.send_message(message.chat.id, f'Информация о клиенте с номером: {phone_number}')
            bot.send_message(message.chat.id,
                             f'👱‍♂️Имя: {client.name if client.name else "Не известно"}\n'
                             f'📱Номер телефона: {", ".join([phone_number.number for phone_number in client.phone_numbers])}',
                             )
            if len(client.documents):
                for document in client.documents:
                    with open(document.filename, 'rb') as file:
                        bot.send_photo(message.chat.id, file)
            else:
                bot.send_message(message.chat.id, 'Фото документов отсутствует.')
        else:
            bot.send_message(message.chat.id, 'Нет клиента с таким номером телефона. Попробуйте еще раз')
            bot.register_next_step_handler(message, get_client_number_for_search, bot)


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
    bot.register_message_handler(make_deposit_button,
                                 func=lambda message: message.text == NameOfButton.MAKE_A_DEPOSIT,
                                 pass_bot=True)
    bot.register_message_handler(check_in_button,
                                 func=lambda message: message.text == NameOfButton.CHECK_IN,
                                 pass_bot=True)
    bot.register_message_handler(blacklist,
                                 func=lambda message: message.text == NameOfButton.BLACKLIST,
                                 pass_bot=True)
    bot.register_message_handler(add_or_remove_client_in_blacklist,
                                 func=lambda
                                     message: message.text == NameOfButton.ADD_CLIENT_TO_BLACKLIST or message.text == NameOfButton.REMOVE_CLIENT_FROM_BLACKLIST,
                                 pass_bot=True)
    bot.register_message_handler(show_client_data,
                                 func=lambda message: message.text == NameOfButton.SHOW_CLIENT_DATA,
                                 pass_bot=True)


def register_user_callback_handlers(bot):
    bot.register_callback_query_handler(apartment_callback,
                                        func=lambda call: True,
                                        pass_bot=True)
    bot.register_callback_query_handler(is_deposit_paid_callback,
                                        func=lambda call: True,
                                        pass_bot=True)
    bot.register_callback_query_handler(check_in_callback,
                                        func=lambda call: True,
                                        pass_bot=True)
