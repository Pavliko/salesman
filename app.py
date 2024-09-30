import logging

from fastapi import FastAPI
from fastapi.responses import Response

from bot.base import setup_bot, stop_bot, feed_update, WEBHOOK_PATH

from sqlalchemy import select
from db.session import get_session

from bot.salesman import Salesman
from transitions.extensions import GraphMachine
from io import BytesIO

from models.user import User

from contextlib import asynccontextmanager

logging.basicConfig(filemode='a', level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await setup_bot()
    yield
    await stop_bot()

app = FastAPI(openapi_url=None, lifespan=lifespan)

@app.post(WEBHOOK_PATH)
async def bot_webhook(update: dict):
    await feed_update(update)

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