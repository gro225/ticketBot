import asyncpg
import config

async def create_pool():
    return await asyncpg.create_pool(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        host=config.DB_HOST,
        port=config.DB_PORT
    )
