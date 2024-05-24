from aiogram.types import Message
from aiogram.filters.command import Command
from dispatcher import dp

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Hello!")


# Обработчик команды /ticket

