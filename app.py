from fastapi import FastAPI
import time
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message, Update
# from aes_chiper import AESCipher

from sqlalchemy import create_engine, MetaData



TOKEN = os.getenv('TELEGRAM_TOKEN')
K = os.getenv('CAXAP')
DATABASE_URL = os.environ.get("DATABASE_URL")


WEBHOOK_SECRET = TOKEN.split(':')[0]

WEBHOOK_PATH = f"/bot/{WEBHOOK_SECRET}"
RENDER_WEB_SERVICE_NAME = "gotbot.ru"
WEBHOOK_URL = "https://" + RENDER_WEB_SERVICE_NAME + WEBHOOK_PATH

engine = create_engine(DATABASE_URL, echo=True)
metadata = MetaData()
metadata.create_all(engine)

logging.basicConfig(filemode='a', level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI(openapi_url=None)

@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL
        )

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    user_full_name = message.from_user.full_name
    logging.info(f'Start: {user_id} {user_full_name} {time.asctime()}. Message: {message}')
    await message.reply(f"Hello, {user_full_name}!")

@dp.message()
async def main_handler(message: Message):
    try:
        user_id = message.from_user.id
        user_full_name = message.from_user.full_name
        logging.info(f'Main: {user_id} {user_full_name} {time.asctime()}. Message: {message}')
        await message.reply("Hello world!")
    except:
        logging.info(f'Main: {user_id} {user_full_name} {time.asctime()}. Message: {message}. Error in main_handler')
        await message.reply("Something went wrong...")    

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)

@app.on_event("shutdown")
async def on_shutdown():
    await bot.get_session().close()
