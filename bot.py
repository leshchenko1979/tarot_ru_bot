import logging
import os
from datetime import datetime, timezone
from io import BytesIO

import psycopg
from telegram.ext import CommandHandler, Updater

from cards import ADVICE, CARD_OF_THE_DAY, LOVE, SITUATION, get_random_card

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = os.environ.get("PORT", 8443)
TOKEN = os.environ["TOKEN"]
POSTGRES = os.environ["DATABASE_URL"]


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("situation", situation))
    dp.add_handler(CommandHandler("love", love))
    dp.add_handler(CommandHandler("card_of_the_day", card_of_the_day))
    dp.add_handler(CommandHandler("advice", advice))

    # Start the Bot
    updater.start_webhook(
        listen="0.0.0.0",
        port=int(PORT),
        url_path=TOKEN,
        webhook_url="https://tarot-ru-bot.herokuapp.com/" + TOKEN,
    )

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


def start(update, context):
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
    context.bot.send_message(update.message.chat.id, msg)


def send_random_card(bot, chat_id, section):
    name, card, meaning = get_random_card(section)
    bytes = BytesIO()
    card.save(bytes, "PNG")
    bot.send_photo(chat_id, photo=bytes.getvalue(), caption=name)
    for row in meaning:
        bot.send_message(chat_id, row)

    update_last_request(chat_id)


def situation(update, context):
    send_random_card(context.bot, update.message.chat.id, SITUATION)


def love(update, context):
    send_random_card(context.bot, update.message.chat.id, LOVE)


def card_of_the_day(update, context):
    send_random_card(context.bot, update.message.chat.id, CARD_OF_THE_DAY)


def advice(update, context):
    send_random_card(context.bot, update.message.chat.id, ADVICE)


def update_last_request(id):
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


conn = None

if __name__ == "__main__":
    with psycopg.connect(POSTGRES) as conn:
        main()
