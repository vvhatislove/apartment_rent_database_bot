import re
import time
import uuid

from database import Database


async def validate_ukrainian_phone_number(phone_number):
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


async def get_user_existing_or_admin(message, bot, check_admin=False):
    db = Database()
    user = await db.get_user_by_tg_user_id(message.from_user.id)
    if user is None:
        await bot.send_message(message.chat.id, 'Ты не зарегистрирован в системе')
        return None
    else:
        if not user.is_admin and check_admin:
            await bot.send_message(message.chat.id, 'Ты не админ, используй /user_start')
            return None
    return user


def generate_unique_filename():
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())
    filename = f"{timestamp}_{unique_id}"
    return filename
