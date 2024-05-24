import asyncio
from dispatcher import dp, bot
from handlers.scense import *

async def main():
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())

