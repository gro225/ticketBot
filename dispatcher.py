import logging
from aiogram import Bot, Dispatcher
import config

# Конфигурация логирования 
logging.basicConfig(level=logging.INFO)

# Предзапрос 
if not config.BOT_TOKEN:
    exit("No token")

# init
bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
