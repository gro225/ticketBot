import logging
from aiogram import Bot, Dispatcher
import config
from database import create_pool

# Конфигурация логирования 
logging.basicConfig(level=logging.INFO)

# Предзапрос 
if not config.BOT_TOKEN:
    exit("No token provided")

# init
bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

# Соединение с бд
async def on_startup():
    dp['db'] = await create_pool()
