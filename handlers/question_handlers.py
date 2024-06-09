import logging
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dispatcher import dp, bot

# Определение состояний
class TicketGenerationStates(StatesGroup):
    awaiting_questions = State()
    confirm_more_questions = State()
    awaiting_ticket_count = State()

# Клавиатуры
def get_confirmation_keyboard():
    buttons = [
        KeyboardButton(text="Да"),
        KeyboardButton(text="Нет")
    ]
    return ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True, one_time_keyboard=True)

# Проверка наличия пользователя
async def check_user_exists(tg_id):
    from database import db_pool
    
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM students WHERE tg_id = $1", str(tg_id))
        return result

# Проверка наличия учителя
async def check_teacher_exists(login):
    from database import db_pool
    
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM teachers WHERE user_id = $1", login)
        return result

# Обработчик команды /add_questions
@dp.message(Command("add_questions"))
async def start_adding_questions(message: types.Message, state: FSMContext):
    user_data = await check_user_exists(message.from_user.id)
    if not user_data:
        await message.answer("Вы не зарегистрированы.")
        return

    teacher_data = await check_teacher_exists(user_data['login'])
    if teacher_data:
        await message.answer("Введите вопросы, каждый с новой строки:")
        await state.set_state(TicketGenerationStates.awaiting_questions)
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")

@dp.message(TicketGenerationStates.awaiting_questions)
async def process_questions(message: types.Message, state: FSMContext):
    questions = message.text.split('\n')
    await state.update_data(questions=questions)
    await message.answer("Вопросы добавлены. Сколько билетов нужно сгенерировать?")
    await state.set_state(TicketGenerationStates.awaiting_ticket_count)

@dp.message(TicketGenerationStates.awaiting_ticket_count)
async def process_ticket_count(message: types.Message, state: FSMContext):
    try:
        ticket_count = int(message.text)
        data = await state.get_data()
        questions = data.get('questions', [])

        if ticket_count <= 0:
            await message.answer("Количество билетов должно быть положительным числом. Попробуйте снова.")
            return

        user_data = await check_user_exists(message.from_user.id)
        teacher_data = await check_teacher_exists(user_data['login'])
        groups = teacher_data['groups']

        from database import db_pool  
        async with db_pool.acquire() as connection:
            for group in groups:
                students = await connection.fetch(
                    """
                    SELECT s.tg_id 
                    FROM students s
                    JOIN students_to_group stg ON s.id = stg.student_id
                    JOIN groups g ON stg.group_id = g.id
                    WHERE g.name = $1
                    """,
                    group)
                for student in students:
                    ticket_message = generate_ticket_message(questions, ticket_count)
                    await bot.send_message(str(student['tg_id']), ticket_message)

        await message.answer("Билеты успешно сгенерированы и отправлены студентам.")
        await state.clear()

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

def generate_ticket_message(questions, ticket_count):
    from random import shuffle

    shuffle(questions)
    ticket_message = "Ваши вопросы:\n\n"
    for i in range(ticket_count):
        ticket_message += f"Билет {i + 1}:\n"
        for j, question in enumerate(questions[i::ticket_count], 1):
            ticket_message += f"{j}. {question}\n"
        ticket_message += "\n"
    return ticket_message
