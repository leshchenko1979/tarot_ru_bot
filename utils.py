import functools
import logging

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(message)s", level=logging.INFO)


def get_share_button():
    return InlineKeyboardButton(
        "Поделиться с другом",
        url="https://t.me/share/url?url=https%3A//t.me/tarot_ru_bot",
    )


def get_cotd_markup():
    turn_cotd_off = InlineKeyboardButton(
        "Отключить ежедневную карту дня", callback_data="cotd_off"
    )

    markup = InlineKeyboardMarkup()
    markup.add(get_share_button())
    markup.add(turn_cotd_off)
    return markup


def get_basic_markup():
    markup = InlineKeyboardMarkup()
    markup.add(get_share_button())
    return markup


processed_messages = set()


def needs_processing(message: Message) -> bool:
    """Check if the message has not already been processed.

    Also registers the message submitted as processed.

    Args:
        message (Message): the message to check.

    Returns:
        bool: Yes if the message has not already been processed, else False.
    """
    logger.info(
        f"Processing message_id {message.message_id} "
        "in chat {message.chat.id} requested"
    )

    if (message.message_id, message.chat.id) in processed_messages:
        logger.info("This message has already been processed")
        return False
    else:
        processed_messages.add((message.message_id, message.chat.id))
        return True


def log_call(func):
    """Decorator for logging function calls."""

    @functools.wraps(func)
    async def wrapper(*args, **kw):
        logger.info(f"Calling {func.__name__}():")
        return await func(*args, **kw)

    return wrapper
