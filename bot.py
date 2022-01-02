import logging
import os
from datetime import datetime, timezone
from io import BytesIO

import psycopg
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook

from cards import ADVICE, CARD_OF_THE_DAY, LOVE, SITUATION, get_random_card

BOT_TOKEN = os.environ["TOKEN"]
HEROKU_APP_NAME = "tarot-ru-bot"

# webhook настройки
WEBHOOK_HOST = f"https://{HEROKU_APP_NAME}.herokuapp.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# webserver настройки
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 8443))

DATABASE_URL = os.environ["DATABASE_URL"]

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(message)s", level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


async def on_startup(dp):
    await bot.delete_webhook(dp)
    await bot.set_webhook(WEBHOOK_URL)

    global conn
    conn = psycopg.connect(DATABASE_URL)


async def on_shutdown(dp):
    conn.close()


@dp.message_handler(commands="start")
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
    command = message.get_command().lower()

    logger.info("Processing command %s", command)

    section = {
        "/situation": SITUATION,
        "/love": LOVE,
        "/card_of_the_day": CARD_OF_THE_DAY,
        "/advice": ADVICE,
    }[command]

    chat_id = message.chat.id

    name, card, meaning = get_random_card(section)

    bytes = BytesIO()
    card.save(bytes, "PNG")
    await bot.send_photo(chat_id, photo=bytes.getvalue(), caption=name)

    for row in meaning:
        await bot.send_message(chat_id, row)

    await update_last_request(chat_id)


async def update_last_request(id):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, last_request) VALUES (%(id)s, %(last_request)s)
            ON CONFLICT (id) DO UPDATE SET last_request = %(last_request)s
            """,
            {"id": id, "last_request": datetime.now(timezone.utc)},
        )
    conn.commit()


start_webhook(
    dispatcher=dp,
    webhook_path=WEBHOOK_PATH,
    on_startup=on_startup,
    on_shutdown=on_shutdown,
    skip_updates=False,
    host=WEBAPP_HOST,
    port=WEBAPP_PORT,
)
