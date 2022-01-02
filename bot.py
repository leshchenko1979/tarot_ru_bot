import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
import os
#в переменных среды Heroku заданы TOKEN и HEROKU_APP_NAME
BOT_TOKEN = os.getenv('TOKEN')
HEROKU_APP_NAME = os.getenv('HEROKU_APP_NAME')
# webhook настройки
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{BOT_TOKEN}'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
# webserver настройки
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.environ.get('PORT', '8443'))
loop = asyncio.get_event_loop()
bot = Bot(token=BOT_TOKEN, loop=loop)
dp = Dispatcher(bot)
#просто повтор сказанного пользователем
@dp.message_handler()
async def echo(message: types.Message):
    await bot.send_message(message.chat.id, message.text)
async def on_startup(dp):
    await bot.delete_webhook(dp)
    await bot.set_webhook(WEBHOOK_URL)
    # и дальше все что надо после запуска
async def on_shutdown(dp):
    # если что-то надо для окончания
    pass
if __name__ == '__main__':
    start_webhook(dispatcher=dp, webhook_path=WEBHOOK_PATH, on_startup=on_startup, on_shutdown=on_shutdown,
                  skip_updates=True, host=WEBAPP_HOST, port=WEBAPP_PORT)
