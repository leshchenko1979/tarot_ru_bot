import logging
from telegram.ext import Updater, CommandHandler
import os
from io import BytesIO

from cards import get_random_card

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

PORT = os.environ.get('PORT', 8443)
TOKEN = os.environ["TOKEN"]


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("situation", situation))

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


def situation(update, context):
    name, card = get_random_card()
    bytes = BytesIO()
    card.save(bytes, "PNG")
    context.bot.send_photo(update.message.chat.id, photo=bytes, caption=name)


if __name__ == "__main__":
    main()
