from database.methods.main import DatabaseGetMethods


async def get_user_existing_or_admin(message, bot, check_admin=False):
    db_get = DatabaseGetMethods()
    user = await db_get.get_user_by_tg_user_id(message.from_user.id)
    if user is None:
        await bot.send_message(message.chat.id, 'Ты не зарегистрирован в системе')
        return None
    else:
        if not user.is_admin and check_admin:
            await bot.send_message(message.chat.id, 'Ты не админ, используй /user_start')
            return None
    return user
