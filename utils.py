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


processed_msg_ids = set()


def needs_processing(message: Message):
    if message.message_id in processed_msg_ids:
        logger.info("This message has already been processed")
        return False
    else:
        processed_msg_ids.add(message.message_id)
        return True
