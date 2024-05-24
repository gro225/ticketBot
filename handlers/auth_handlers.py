from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from dispatcher import dp, db_pool

# Проверка наличия пользователя
async def check_user_exists(tg_id):
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM users WHERE tg_id = $1", tg_id)
        return result

# Проверка наличия учителя
async def check_teacher_exists(user_id):
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM teachers WHERE id = $1", user_id)
        return result

# Обновление групп учителя
async def update_teacher_groups(user_id, groups):
    async with db_pool.acquire() as connection:
        await connection.execute("UPDATE teachers SET groups = $1 WHERE id = $2", groups, user_id)

# Обновление tg_id
async def update_tg_id(user_id: int, tg_id: int):
    async with db_pool.acquire() as connection:
        await connection.execute("UPDATE users SET tg_id = $1 WHERE id = $2", tg_id, user_id)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_data = await check_user_exists(message.from_user.id)
    
    if user_data:
        teacher_data = await check_teacher_exists(user_data['id'])
        if teacher_data:
            if not teacher_data['groups']:
                await message.answer("Пожалуйста, введите группы, в которых вы преподаете.")
                await state.set_state("awaiting_groups")
            else:
                await message.answer("Вы авторизованы как учитель.")
        else:
            await message.answer("Вы авторизованы как студент.")
    else:
        await message.answer("Введите ваш никнейм для регистрации:")
        await state.set_state("awaiting_username")

@dp.message(state="awaiting_username")
async def process_username(message: types.Message, state: FSMContext):
    user_id = message.text
    async with db_pool.acquire() as connection:
        user_exists = await connection.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
    
    if user_exists:
        user_id = user_exists['id']
        await update_tg_id(user_id, message.from_user.id)
        await message.answer("Вы успешно зарегистрированы.")
        await state.finish()
    else:
        await message.answer("Никнейм не найден в базе данных.")

@dp.message(state="awaiting_groups")
async def process_groups(message: types.Message, state: FSMContext):
    groups = message.text.split(',')
    user_data = await check_user_exists(message.from_user.id)
    await update_teacher_groups(user_data['id'], groups)
    await message.answer("Группы успешно обновлены.")
    await state.finish()
