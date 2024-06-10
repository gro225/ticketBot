import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
from dispatcher import dp

# Определение состояний
class AuthStates(StatesGroup):
    awaiting_login = State()
    awaiting_groups = State()

# Проверка наличия tg_id
async def check_user_tg(tg_id):
    from database import db_pool  

    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    logging.info(f"db_pool в check_user_exists: {db_pool}")
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT login FROM students WHERE tg_id = $1", str(tg_id))
        return result

# Проверка наличия пользователя
async def check_user(login):
    from database import db_pool  
    logging.info(f"db_pool в check_user_exists: {db_pool}")
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM students WHERE login = $1", login)
        return result

# Проверка наличия учителя и его групп
async def check_teacher_and_groups(login):
    from database import db_pool  
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    async with db_pool.acquire() as connection:
        teacher_data = await connection.fetchrow("SELECT * FROM teachers WHERE user_id = $1", login)
        if teacher_data:
            groups = teacher_data.get('groups', [])
            if not groups:
                return None, True
            else:
                return teacher_data, False
        else:
            return None, False

# Обновление групп учителя
async def update_teacher_groups(login, groups):
    from database import db_pool  
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return
    
    async with db_pool.acquire() as connection:
        await connection.execute("UPDATE students SET groups = $1 WHERE user_id = $2", groups, login)

# Обновление tg_id
async def update_tg_id(login, tg_id):
    from database import db_pool
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return
    
    async with db_pool.acquire() as connection:
        await connection.execute("UPDATE students SET tg_id = $1 WHERE login = $2", str(tg_id), login)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_data = await check_user_tg(message.from_user.id)
    
    if user_data:
        await message.answer("Добро пожаловать!")
    else:
        await message.answer("Введите ваш логин для регистрации:")
        await state.set_state(AuthStates.awaiting_login)

@dp.message(AuthStates.awaiting_login)
async def process_login(message: types.Message, state: FSMContext):
    login = message.text
    user_data = await check_user(login)
    
    if user_data:
        await update_tg_id(login, message.from_user.id)
        
        teacher_data, no_groups = await check_teacher_and_groups(login)
        if teacher_data:
            if no_groups:
                await message.answer("Пожалуйста, введите группы, в которых вы преподаете, через запятую:")
                await state.set_state(AuthStates.awaiting_groups)
            else:
                await message.answer("Вы авторизованы как учитель.")
        else:
            await message.answer("Вы авторизованы как студент.")
        await state.clear()
    else:
        await message.answer("Логин не найден в базе данных. Попробуйте еще раз.")

@dp.message(AuthStates.awaiting_groups)
async def process_groups(message: types.Message, state: FSMContext):
    groups = message.text.split(',')
    user_data = await state.get_data()
    login = user_data.get('login')
    
    if login:
        await update_teacher_groups(login, groups)
        await message.answer("Группы успешно обновлены.")
        await state.clear()
    else:
        await message.answer("Произошла ошибка. Попробуйте еще раз.")
