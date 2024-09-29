import time
import logging
import os

from fastapi import FastAPI
from fastapi.responses import Response

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, Update, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, CallbackQuery
# from aes_chiper import AESCipher

from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from salesman import Salesman
from transitions.extensions import GraphMachine
from io import BytesIO

from models.user import User, Base

from contextlib import asynccontextmanager



TOKEN = os.getenv('TELEGRAM_TOKEN')
K = os.getenv('CAXAP')
DATABASE_URL = os.environ.get("DATABASE_URL")


WEBHOOK_SECRET = TOKEN.split(':')[0]

WEBHOOK_PATH = f"/bot/{WEBHOOK_SECRET}"
RENDER_WEB_SERVICE_NAME = "gotbot.ru"
WEBHOOK_URL = "https://" + RENDER_WEB_SERVICE_NAME + WEBHOOK_PATH

engine = create_async_engine(DATABASE_URL, echo=True)

# Создание сессии
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@asynccontextmanager
async def get_session():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


logging.basicConfig(filemode='a', level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = FastAPI(openapi_url=None)

@app.on_event("startup")
async def on_startup():
    await bot.set_my_commands([BotCommand(command="menu", description="Меню")])
    
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(
            url=WEBHOOK_URL
        )

@dp.message(Command(commands=["start", "menu"]))
async def start_handler(message: Message):
    logging.info(f'Start message: {message}')

    try:
        user = await get_user_and_set_message_id(message.from_user.id, message.message_id) 
        await message.answer(f"Hello,!!!", reply_markup=repry_keyboard_markup())
    except:
        await message.reply("Something went wrong...") 

@dp.message()
async def main_handler(message: Message):
    logging.info(f'Message: {message}')

    try:
        user = await get_user_and_set_message_id(message.from_user.id, message.message_id)
        await message.reply("Hello world!")
    except:
        await message.reply("Something went wrong...")    

@dp.callback_query()
async def process_callback_button(callback_query: CallbackQuery):
    logging.info(f'callback: {callback_query}')
    try:
        user = await get_user_and_set_message_id(callback_query.from_user.id, callback_query.message.message_id)
        await callback_query.answer("Button submitted...") 
        await callback_query.message.edit_text("DONE") 
    except:
        await callback_query.answer("Something went wrong...")  

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)

@app.get("/image")
async def get_image():
    async with get_session() as session:
        result = await session.execute(select(User).fetch(1))
        model = Salesman(result.scalars().first())
        machine = GraphMachine(model=model, states=Salesman.states, transitions=Salesman.transitions, initial='waiting_start')
        stream = BytesIO()
        machine.get_graph().draw(stream, prog='dot', format='png')
        stream.seek(0)
        image_data = stream.read()
        return Response(content=image_data, media_type="image/png")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.get_session().close()

async def get_user_and_set_message_id(telegram_id, message_id):
    async with get_session() as session:
        user = await get_or_create_user(telegram_id, session)
        user.last_message_id = message_id
    return user

async def get_or_create_user(telegram_id, session):
    # Поиск пользователя по telegram_id
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id).fetch(1)
    )
    user = result.scalars().first()
    
    if user:
        logging.info(f"Пользователь с telegram_id {telegram_id} найден: {user}")
    else:
        # Если пользователь не найден, создаем нового
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.commit()
        logging.info(f"Создан новый пользователь с telegram_id {telegram_id}")
    
    return user

def repry_keyboard_markup():
    # Создаем кнопки
    button_menu = InlineKeyboardButton(text='Настройки', callback_data='settings')

    # Создаем клавиатуру и добавляем в нее кнопки
    return InlineKeyboardMarkup(inline_keyboard=[[button_menu]])