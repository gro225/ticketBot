import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import config
from database import create_pool

# Конфигурация логирования 
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

# Подключение к базе данных
db_pool = None


async def on_startup():
    global db_pool
    db_pool = await create_pool()

async def on_shutdown():
    await db_pool.close()

# Для безопасного закрытия
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)
