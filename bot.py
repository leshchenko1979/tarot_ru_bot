import logging
import os
from asyncio import ALL_COMPLETED, run, sleep, wait
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


async def start_wh():
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=False,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )


async def on_startup(dp):
    await bot.delete_webhook(dp)
    await bot.set_webhook(WEBHOOK_URL)

    global aconn
    aconn = await psycopg.AsyncConnection.connect(DATABASE_URL)


async def on_shutdown(dp):
    await aconn.close()


async def send_cotd():
    await sleep(10)  # wait until the connection is established

    while True:
        async with aconn.cursor() as cur:
            await cur.execute(
                """
                SELECT id FROM users
                WHERE last_cotd < now() - interval '1 day' AND send_cotd = 1
                """
            )
            ids = await cur.fetchall()

            for id in ids:
                await wait(
                    [
                        send_random_card(id, CARD_OF_THE_DAY),
                        update_last_cotd(id, cur),
                        sleep(2),
                    ],
                    return_when=ALL_COMPLETED,
                )
        await sleep(3600)  # wait for an hour then repeat


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

    id = message.chat.id

    await send_random_card(id, section)
    await update_last_request(id)


async def send_random_card(id, section):
    name, card, meaning = get_random_card(section)

    bytes = BytesIO()
    card.save(bytes, "PNG")
    await bot.send_photo(id, photo=bytes.getvalue(), caption=name)

    for row in meaning:
        await bot.send_message(id, row)


async def update_last_request(id):
    async with aconn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO users (id, last_request) VALUES (%(id)s, %(last_request)s)
            ON CONFLICT (id) DO UPDATE SET last_request = %(last_request)s
            """,
            {"id": id, "last_request": datetime.now(timezone.utc)},
        )
    await aconn.commit()


async def update_last_cotd(id, cur):
    await cur.execute("UPDATE users SET last_cotd = now() WHERE id = %s", id)
    await aconn.commit()


run(wait([start_wh(), send_cotd()], return_when=ALL_COMPLETED))
