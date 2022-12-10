import asyncio
import datetime as dt
import logging
import os
from asyncio import gather, sleep
from io import BytesIO

import aiogram
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher

import db
import utils
from cards import ADVICE, CARD_OF_THE_DAY, LOVE, SITUATION, get_random_card

BOT_TOKEN = os.environ["TOKEN"]

# Enable logging
logger = logging.getLogger(__name__)
logging.basicConfig(format="%(message)s", level=logging.INFO)

logger.info("Starting the main module")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


def main(request):
    asyncio.run(main_async(request))
    return "ok"


async def main_async(request):
    await db.set_up_db_connection()

    Bot.set_current(dp.bot)
    update = types.Update.to_object(request.get_json())
    await gather(dp.process_update(update), send_all_daily_cotds())


@utils.log_call
async def send_all_daily_cotds():
    while True:
        now = dt.datetime.now(dt.timezone.utc)
        this_morning = dt.datetime.combine(now.date(), dt.time(6, 0), dt.timezone.utc)

        if now < this_morning:
            break

        async for chat_id in db.next_daily_cotd(this_morning):
            await gather(
                send_single_daily_cotd(chat_id), db.update_last_cotd(chat_id), sleep(2)
            )

        next_morning = this_morning + dt.timedelta(days=1)
        await sleep((next_morning - now).total_seconds())


@utils.log_call
async def send_single_daily_cotd(chat_id):
    try:
        await bot.send_message(chat_id, "Ваша сегодняшняя карта дня:")
        await send_random_card(chat_id, CARD_OF_THE_DAY, utils.get_cotd_markup())
    except aiogram.utils.exceptions.BotBlocked:
        logger.info(f"Bot blocked by {chat_id}")
        await db.mark_blocked(chat_id)


async def send_random_card(chat_id, section, markup):
    name, card, meaning = get_random_card(section)

    card_image = BytesIO()
    card.save(card_image, "PNG")
    await bot.send_photo(chat_id, photo=card_image.getvalue(), caption=name)

    for i, row in enumerate(meaning):
        if i == len(meaning) - 1 and markup:
            await bot.send_message(chat_id, row, reply_markup=markup)
        else:
            await bot.send_message(chat_id, row)


@dp.callback_query_handler(text="cotd_off")
@utils.log_call
async def turn_cotd_off(cbq: types.CallbackQuery):
    if not utils.needs_processing(cbq.message):
        return

    await gather(
        bot.answer_callback_query(cbq.id), switch_cotd(cbq.from_user.id, "/cotd_off")
    )


@dp.message_handler(commands="start")
@utils.log_call
async def start(message: types.Message):
    if not utils.needs_processing(message):
        return

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

    await gather(bot.send_message(chat_id, msg), db.update_last_request(chat_id))


@dp.message_handler(commands=["situation", "love", "card_of_the_day", "advice"])
@utils.log_call
async def process_command(message: types.Message):
    if not utils.needs_processing(message):
        return

    command = message.get_command().lower()

    logger.info("Processing command %s", command)

    section = {
        "/situation": SITUATION,
        "/love": LOVE,
        "/card_of_the_day": CARD_OF_THE_DAY,
        "/advice": ADVICE,
    }[command]

    chat_id = message.chat.id

    if section == CARD_OF_THE_DAY and await db.cotd_sent_today(chat_id):
        await bot.send_message(
            chat_id,
            "Карта дня уже отправлялась сегодня. Не гневите судьбу, дождитесь завтра!",
        )
        return

    ops = [
        send_random_card(chat_id, section, utils.get_basic_markup()),
        db.update_last_request(chat_id),
    ]

    if section == CARD_OF_THE_DAY:
        ops.append(db.update_last_cotd(chat_id))

    await gather(*ops)


@dp.message_handler(commands=["cotd_on", "cotd_off"])
@utils.log_call
async def process_cotd_command(message: types.Message):
    if not utils.needs_processing(message):
        return

    chat_id = message.chat.id
    command = message.get_command().lower()
    await switch_cotd(chat_id, command)


async def switch_cotd(chat_id, command: str):
    new_send_cotd_setting, new_state_label = {
        "/cotd_on": (1, "включена"),
        "/cotd_off": (0, "отключена"),
    }[command]

    await gather(
        bot.send_message(chat_id, f"Ежедневная отправка карты дня {new_state_label}"),
        db.save_send_cotd_setting(chat_id, new_send_cotd_setting),
        db.update_last_request(chat_id),
    )
