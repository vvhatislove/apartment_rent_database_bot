import re
import time
import uuid
from datetime import datetime

from bot.buttons import NameOfButton
from database import Database

USER_START_MENU = [NameOfButton.ADD_NEW_LEASE_ENTRY,
                   NameOfButton.MAKE_A_DEPOSIT,
                   NameOfButton.CHECK_IN,
                   NameOfButton.BLACKLIST,
                   NameOfButton.SHOW_CLIENT_DATA,
                   NameOfButton.FIND_LEASE_ENTRY]


def validate_ukrainian_phone_number(phone_number):
    cleaned_number = re.sub(r'\D', '', phone_number)

    if len(cleaned_number) == 10:
        if cleaned_number.startswith('0'):
            cleaned_number = '+38' + cleaned_number
        elif cleaned_number.startswith('380'):
            cleaned_number = '+' + cleaned_number
        else:
            return None
    elif len(cleaned_number) == 12 and cleaned_number.startswith('+38'):
        pass
    else:
        return None

    return cleaned_number


def get_user_existing_or_admin(message, bot, check_admin=False):
    db = Database()
    user = db.get_user_by_tg_user_id(message.from_user.id)
    if user is None:
        bot.send_message(message.chat.id, 'Ты не зарегистрирован в системе')
        return None
    else:
        if not user.is_admin and check_admin:
            bot.send_message(message.chat.id, 'Ты не админ, используй /user_start')
            return None
    return user


def generate_unique_filename():
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())
    filename = f"{timestamp}_{unique_id}"
    return filename


def check_date_format(date_str):
    # Разбиваем строку на компоненты
    date_components = date_str.split('/')

    # Если компонентов не два, значит формат даты неверен
    if len(date_components) != 2:
        return None

    # Если год не существует в строке, добавляем текущий год
    if len(date_components[0].split('.')) == 2:
        date_components[0] += f'.{datetime.now().year}'

    try:
        # Пытаемся создать объект datetime
        dt = datetime.strptime('/'.join(date_components), "%d.%m.%Y/%H:%M")

        # Проверяем, что дата больше текущей даты
        return dt

    except ValueError:
        # Если возникает ошибка, значит формат даты неверен
        return None


def parse_date_values(date_str):
    date_format = "%d.%m.%Y:%H.%M"
    start_str, end_str = date_str.split('-')
    start_date = datetime.strptime(start_str, date_format)
    end_date = datetime.strptime(end_str, date_format)
    return start_date, end_date


def get_lease_info(lease):
    phone_numbers = ", ".join([phone.number for phone in lease.client.phone_numbers])
    num_documents = len(lease.client.documents) if lease.client.documents else 0
    return f'👨Клиент: {lease.client.name if lease.client.name else "Не известно"}\n' \
           f'📱Номера телефонов клиента: {phone_numbers}\n' \
           f'📑Кол-во фотографий документов: {num_documents}\n' \
           f'🏠Адрес сдаваемой квартиры: {lease.apartment.address}\n' \
           f'📅Период сдачи:{lease.start_date.strftime("%d.%m.%Y | %H:%M")} - {lease.end_date.strftime("%d.%m.%Y | %H:%M")}\n' \
           f'💵Сумма арендной платы: {lease.rent_amount}\n' \
           f'💸Сумма залога: {lease.deposit}\n\n' \
           f'✍️Комментарий: {lease.additional_details}\n' \
           f'------------------------------------'
