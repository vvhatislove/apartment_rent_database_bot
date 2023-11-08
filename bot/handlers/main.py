from bot.handlers.admin import register_admin_handlers
from bot.handlers.other import register_other_handlers
from bot.handlers.user import register_user_handlers, register_user_callback_handlers


def register_all_handlers(bot) -> None:
    handlers = (
        register_other_handlers,
        register_user_handlers,
        register_admin_handlers,
        register_user_callback_handlers
    )
    for handler in handlers:
        handler(bot)
