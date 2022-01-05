import logging
import os
from asyncio import create_task, gather, sleep
import datetime as dt
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

    global aconn
    aconn = await psycopg.AsyncConnection.connect(DATABASE_URL)

    create_task(send_cotd())


async def on_shutdown(dp):
    await aconn.close()


async def send_cotd():
    while True:
        logger.info("Starting sending cards of the day")

        now = dt.datetime.now(dt.timezone.utc)
        this_morning = dt.datetime.combine(now.date(), dt.time(6, 0), dt.timezone.utc)

        if now < this_morning:
            break

        async with aconn.cursor() as cur:
            while True:
                await cur.execute(
                    """
                    SELECT id FROM users
                    WHERE last_cotd < %(this_morning)s AND send_cotd = 1
                    LIMIT 1
                    """,
                    {"this_morning": this_morning},
                )
                record = await cur.fetchone()

                if not record:
                    break

                id = record[0]
                logger.info("Sending the card of the day to %s", id)
                await gather(
                    send_daily_cotd(id),
                    update_last_cotd(id, cur),
                    sleep(2),
                )

        next_morning = this_morning + dt.timedelta(days=1)
        await sleep((next_morning - now).total_seconds())


async def send_daily_cotd(id):
    await bot.send_message(id, "Ваша сегодняшняя карта дня:")
    await send_random_card(id, CARD_OF_THE_DAY)
    await bot.send_message(id, "(Отключить ежедневную карту дня: /cotd_off)")


@dp.message_handler(commands="start")
async def start(message: types.Message):
    msg = "\n".join(
        [
            "/start - вывести это сообщение",
            "",
            "/situation - расклад на ситуацию",
            "/love - расклад на отношения",
            "/card_of_the_day - карта дня",
            "/advice - совет карты",
            "",
            "/cotd_on - включить ежедневную отправку карты дня",
            "/cotd_off - отключить ежедневную отправку карты дня",
            "",
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

    await gather(send_random_card(id, section), update_last_request(id))


async def send_random_card(id, section):
    name, card, meaning = get_random_card(section)

    bytes = BytesIO()
    card.save(bytes, "PNG")
    await bot.send_photo(id, photo=bytes.getvalue(), caption=name)

    for row in meaning:
        await bot.send_message(id, row)


@dp.message_handler(commands=["cotd_on", "cotd_off"])
async def switch_cotd(message: types.Message):
    command = message.get_command().lower()

    new_send_cotd_setting, new_state_label = {
        "/cotd_on": (1, "включена"),
        "/cotd_off": (0, "отключена"),
    }[command]

    id = message.chat.id

    await gather(
        save_send_cotd_setting(id, new_send_cotd_setting),
        bot.send_message(id, "Ежедневная отправка карты дня %s" % new_state_label),
        update_last_request(id),
    )


async def save_send_cotd_setting(id, new_setting):
    async with aconn.cursor() as cur:
        await cur.execute(
            """
            UPDATE users SET
                send_cotd = %(new_setting)s,
                last_cotd = now()
            WHERE id = %(id)s
            """,
            {"new_setting": new_setting, "id": id},
        )
    await aconn.commit()


async def update_last_request(id):
    async with aconn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO users (id, last_request, last_cotd, send_cotd)
            VALUES (%(id)s, now(), now(), 1)
            ON CONFLICT (id) DO UPDATE SET last_request = now()
            """,
            {"id": id},
        )
    await aconn.commit()


async def update_last_cotd(id, cur):
    await cur.execute(
        "UPDATE users SET last_cotd = now() WHERE id = %(id)s", {"id": id}
    )
    await aconn.commit()


start_webhook(
    dispatcher=dp,
    webhook_path=WEBHOOK_PATH,
    on_startup=on_startup,
    on_shutdown=on_shutdown,
    skip_updates=False,
    host=WEBAPP_HOST,
    port=WEBAPP_PORT,
)
