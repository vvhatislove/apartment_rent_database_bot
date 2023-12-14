def beep(chat_id, bot) -> None:
    """Send the beep message."""
    bot.send_message(chat_id, text='Beep!')
