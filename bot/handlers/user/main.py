import asyncio
import random
from datetime import datetime

from telebot import types
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from bot.buttons import NameOfButton
from bot.handlers.utils import get_user_existing_or_admin, validate_ukrainian_phone_number, generate_unique_filename
from bot.keyboard.reply.main import ReplyKeyboard
from bot.states.main import AddNewLeaseState
from database import Database


async def user_start_command(message: Message, bot: AsyncTeleBot):
    user = await get_user_existing_or_admin(message, bot)
    if user is None:
        return
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.ADD_NEW_LEASE)
    # NameOfButton.DELETE_ENTRY,
    # NameOfButton.EDIT_ENTRY,
    # NameOfButton.FIND_ENTRY,
    # NameOfButton.UPLOAD_TO_EXCEL)

    await bot.send_message(message.chat.id, f'Привет пользователь {user.name}', reply_markup=keyboard)


async def add_new_lease_button(message: Message, bot: AsyncTeleBot):
    user = await get_user_existing_or_admin(message, bot)
    if user is None:
        return
    await bot.send_message(message.chat.id, 'Напишите номер телефона клиента📱',
                           reply_markup=types.ReplyKeyboardRemove())
    await bot.set_state(message.from_user.id, AddNewLeaseState.add_client_number, message.chat.id)


async def add_client_number(message: Message, bot: AsyncTeleBot):
    phone_number = await validate_ukrainian_phone_number(message.text)
    if phone_number is None:
        await bot.send_message(message.chat.id, 'Вы ввели некорректный номер телефона📵\n\nВведите правильный номер')
    else:
        db = Database()
        client = await db.get_client_by_phone_number(phone_number)
        if client is None:
            await bot.send_message(message.chat.id, 'В базе нет клиента, с таким номером телефона📖.\nСоздаем нового✍️.')
            await bot.send_message(message.chat.id, 'Отправьте мне имя и фамилию клиента👱‍♂️')
            async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['phone_number'] = phone_number
            await bot.set_state(message.from_user.id, AddNewLeaseState.get_client_name, message.chat.id)
        else:
            await bot.send_message(message.chat.id, '⚠️Такой клиент уже добавлен в базу!\n\n'
                                                    f'👱‍♂️Имя: {client.name}\n'
                                                    f'📱Номер телефона: {", ".join([phone_number.number for phone_number in client.phone_numbers])}')


async def get_client_name(message: Message, bot: AsyncTeleBot):
    client_name = message.text
    keyboard = ReplyKeyboard.get_reply_keyboard(NameOfButton.CONFIRM_PHOTOS_UPLOADING)
    await bot.send_message(message.chat.id, 'Теперь пришлите фотографию его документов📑.')
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['client_name'] = client_name
    await bot.set_state(message.from_user.id, AddNewLeaseState.get_document_photos, message.chat.id)


async def get_document_photos_and_add_client_into_db(message: Message, bot: AsyncTeleBot):
    # path_image = f'doc_images/{generate_unique_filename()}.jpg'
    # file_info = await bot.get_file(message.photo[-1].file_id)
    # downloaded_file = await bot.download_file(file_info.file_path)
    # with open(path_image, 'wb') as new_file:
    #     new_file.write(downloaded_file)
    await bot.send_message(message.chat.id, 'Изображение загружено')
    path_image = 'test'
    async with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        client_name = data.get('client_name')
        phone_number = data.get('phone_number')
    db = Database()
    await db.add_client(client_name, [phone_number], [path_image])
    # await bot.set_state(message.from_user.id, AddNewLeaseState.add_apartment_address, message.chat.id)
    await bot.send_message(message.chat.id, '🆕Новый клиент\n\n'
                                f'👱‍♂️Имя: {client_name}\n'
                                f'📱Номер телефона: {phone_number}\n\n'
                                '✅Успешно добавлен')
    await ask_apartment_address(message, bot)


async def ask_apartment_address(message: Message, bot: AsyncTeleBot):
    db = Database()
    apartments = await db.get_all_apartments()
    markup = types.InlineKeyboardMarkup()
    for apartment in apartments:
        markup.add(types.InlineKeyboardButton(apartment.address, callback_data=apartment))
    markup.add(types.InlineKeyboardButton('Добавить новый адрес', callback_data='Добавить новый адрес'))
    await bot.send_message(message.chat.id, 'Выберете адрес или создайте новый.', reply_markup=markup)
    await bot.send_message(message.chat.id, 'sdada')
    await bot.send_message(message.chat.id, 'sdada')
    await bot.send_message(message.chat.id, 'sdada')
    await bot.send_message(message.chat.id, 'sdada')


async def get_apartment_address(call, bot: AsyncTeleBot):
    print(type(call))


def register_user_handlers(bot):
    bot.register_message_handler(user_start_command,
                                 commands=['user_start'],
                                 pass_bot=True)

    bot.register_message_handler(add_new_lease_button,
                                 func=lambda message: message.text == NameOfButton.ADD_NEW_LEASE,
                                 pass_bot=True)

    bot.register_message_handler(add_client_number,
                                 state=AddNewLeaseState.add_client_number,
                                 pass_bot=True
                                 )
    bot.register_message_handler(get_client_name,
                                 state=AddNewLeaseState.get_client_name,
                                 pass_bot=True
                                 )
    bot.register_message_handler(get_document_photos_and_add_client_into_db,
                                 content_types=['photo'],
                                 state=AddNewLeaseState.get_document_photos,
                                 pass_bot=True
                                 )
    bot.register_message_handler(get_apartment_address,
                                 state=AddNewLeaseState.add_apartment_address,
                                 pass_bot=True
                                 )


def register_user_callback_handlers(bot):
    bot.register_callback_query_handler(get_apartment_address,
                                        func=lambda call: True,
                                        pass_bot=True)
