import logging
import os
from datetime import datetime, timezone
from io import BytesIO

import psycopg
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook

from cards import ADVICE, CARD_OF_THE_DAY, LOVE, SITUATION, get_random_card

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = os.environ.get("PORT", 8443)
TOKEN = os.environ["TOKEN"]
POSTGRES = os.environ["POSTGRES"]

WEBHOOK_URL = "https://tarot-ru-bot.herokuapp.com/" + TOKEN

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


async def on_startup(dp):
    global conn
    conn = psycopg.connect(POSTGRES)
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    conn.close()


start_webhook(
    dispatcher=dp,
    webhook_path=WEBHOOK_URL,
    on_startup=on_startup,
    on_shutdown=on_shutdown,
    skip_updates=True,
    host="0.0.0.0",
    port=PORT,
)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    msg = "\n\n".join(
        [
            "/start - вывести это сообщение",
            "/situation - расклад на ситуацию",
            "/love - расклад на отношения",
            "/card_of_the_day - карта дня",
            "/advice - совет карты",
            "Связаться с автором: @leshchenko1979",
        ]
    )

    chat_id = message.chat.id

    await bot.send_message(chat_id, msg)
    await update_last_request(chat_id)


@dp.message_handler(commands=["situation", "love", "card_of_the_day", "advice"])
async def process_command(message: types.Message):
    section = {
        "situation": SITUATION,
        "love": LOVE,
        "card_of_the_day": CARD_OF_THE_DAY,
        "advice": ADVICE,
    }[message.get_command().lower()]

    chat_id = message.chat.id

    name, card, meaning = get_random_card(section)

    bytes = BytesIO()
    card.save(bytes, "PNG")
    await bot.send_photo(chat_id, photo=bytes.getvalue(), caption=name)

    for row in meaning:
        await bot.send_message(chat_id, row)

    await update_last_request(chat_id)


async def update_last_request(id):
    global conn
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, last_request) VALUES (%(id)s, %(last_request)s)
            ON CONFLICT (id) DO UPDATE SET last_request = %(last_request)s
            """,
            {"id": id, "last_request": datetime.now(timezone.utc)},
        )
    conn.commit()
