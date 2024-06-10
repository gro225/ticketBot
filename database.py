import logging
import asyncpg
import config

async def create_pool():
    return await asyncpg.create_pool(dsn=config.DB_URL)

db_pool = None

async def on_startup():
    global db_pool
    logging.info("Запуск on_startup")
    try:
        db_pool = await asyncpg.create_pool(config.DB_URL)
        logging.info("Подключение к базе данных установлено.")
    except Exception as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")

async def on_shutdown():
    logging.info("Запуск on_shutdown")
    if db_pool:
        await db_pool.close()
        logging.info("Подключение к базе данных закрыто.")
