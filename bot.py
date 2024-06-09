import asyncio
import logging
from dispatcher import dp, bot
from database import on_startup, on_shutdown
import handlers.auth_handlers
import handlers.question_handlers


async def main():
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

