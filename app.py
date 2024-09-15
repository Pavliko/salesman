import logging
import os

from aiogram import types, Dispatcher, Bot
from aiogram.types import WebAppInfo
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse

load_dotenv()

TOKEN = os.environ["TELEGRAM_TOKEN"]

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World!!!"}
