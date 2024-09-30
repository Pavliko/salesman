import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, CallbackQuery, Update

from sqlalchemy import select
from db.session import get_session
from models.user import User


TOKEN = os.getenv('TELEGRAM_TOKEN')
WEBHOOK_SECRET = TOKEN.split(':')[0]
WEBHOOK_PATH = f"/bot/{WEBHOOK_SECRET}"
RENDER_WEB_SERVICE_NAME = "gotbot.ru"
WEBHOOK_URL = "https://" + RENDER_WEB_SERVICE_NAME + WEBHOOK_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher()

async def setup_bot():
    await bot.set_my_commands([BotCommand(command="menu", description="Меню")])
    
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL)

async def stop_bot():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.get_session().close()

async def feed_update(update: dict):
    telegram_update = Update(**update)
    await dp.feed_update(bot, telegram_update)


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