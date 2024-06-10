import logging
import aiohttp
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.command import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dispatcher import dp, bot

class TicketGenerationStates(StatesGroup):
    awaiting_questions_list = State()
    confirm_more_questions = State()
    awaiting_ticket_count = State()
    awaiting_questions_per_ticket = State()

def get_confirmation_keyboard():
    buttons = [
        KeyboardButton(text="Да"),
        KeyboardButton(text="Нет")
    ]
    return ReplyKeyboardMarkup(keyboard=[buttons], resize_keyboard=True, one_time_keyboard=True)

async def check_user_exists(tg_id):
    from database import db_pool  
    
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM students WHERE tg_id = $1", str(tg_id))
        return result

async def check_teacher_exists(login):
    from database import db_pool 
    
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        return None
    
    async with db_pool.acquire() as connection:
        result = await connection.fetchrow("SELECT * FROM teachers WHERE user_id = $1", login)
        return result

@dp.message(Command("add_questions"))
async def start_adding_questions(message: types.Message, state: FSMContext):
    user_data = await check_user_exists(message.from_user.id)
    if not user_data:
        await message.answer("Вы не зарегистрированы.")
        return

    teacher_data = await check_teacher_exists(user_data['login'])
    if teacher_data:
        await message.answer("Введите список вопросов, каждый вопрос на новой строке:")
        await state.set_state(TicketGenerationStates.awaiting_questions_list)
        await state.update_data(questions=[])
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")

@dp.message(TicketGenerationStates.awaiting_questions_list)
async def process_questions_list(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('questions', [])

    if message.text.startswith("http"):
        subject_code = extract_subject_code_from_url(message.text)
        print(subject_code)
        if not subject_code:
            await message.answer("Неверная ссылка.")
            return

        new_questions = await fetch_questions_from_api(subject_code)
        if not new_questions:
            await message.answer("Вопросы не найдены для данного предмета.")
            return
    else:
        new_questions = message.text.split('\n')

    questions.extend(new_questions)
    await state.update_data(questions=questions)
    await message.answer("Вопросы добавлены. Хотите добавить еще вопросы?", reply_markup=get_confirmation_keyboard())
    await state.set_state(TicketGenerationStates.confirm_more_questions)

@dp.message(TicketGenerationStates.confirm_more_questions)
async def confirm_more_questions(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        await message.answer("Введите еще список вопросов, каждый вопрос на новой строке:")
        await state.set_state(TicketGenerationStates.awaiting_questions_list)
    elif message.text.lower() == "нет":
        await message.answer("Сколько вопросов должно быть в каждом билете?")
        await state.set_state(TicketGenerationStates.awaiting_questions_per_ticket)
    else:
        await message.answer("Пожалуйста, используйте кнопки для ответа.", reply_markup=get_confirmation_keyboard())

@dp.message(TicketGenerationStates.awaiting_questions_per_ticket)
async def process_questions_per_ticket(message: types.Message, state: FSMContext):
    try:
        questions_per_ticket = int(message.text)
        data = await state.get_data()
        questions = data.get('questions', [])

        if questions_per_ticket <= 0:
            await message.answer("Количество вопросов в билете должно быть положительным числом. Попробуйте снова.")
            return

        await state.update_data(questions_per_ticket=questions_per_ticket)
        await message.answer("Сколько билетов нужно сгенерировать?")
        await state.set_state(TicketGenerationStates.awaiting_ticket_count)
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

@dp.message(TicketGenerationStates.awaiting_ticket_count)
async def process_ticket_count(message: types.Message, state: FSMContext):
    try:
        ticket_count = int(message.text)
        data = await state.get_data()
        questions = data.get('questions', [])
        questions_per_ticket = data.get('questions_per_ticket')

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
                    JOIN students_to_groups stg ON s.id = stg.student_id
                    JOIN groups g ON stg.group_id = g.id
                    WHERE g.name LIKE '%' || $1 || '%'
                    """,
                    group)
                tickets = generate_tickets(questions, questions_per_ticket, ticket_count)
                all_tickets = "\n\n".join(tickets)
                import random
                for student in students:
                    rndnmbr = random.randint(0, len(tickets) - 1)
                    selected_ticket = tickets[rndnmbr]
                    tickets.pop(rndnmbr)
                    try:
                        await bot.send_message(str(student['tg_id']), selected_ticket)
                    except Exception as e:
                        logging.error(f"Ошибка отправки сообщения пользователю {student['tg_id']}: {e}")

        await message.answer("Билеты успешно сгенерированы и отправлены студентам.")
        await bot.send_message(message.from_user.id, f"Сгенерированные билеты:\n\n{all_tickets}")
        await state.clear()

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

def generate_tickets(questions, questions_per_ticket, ticket_count):
    from random import shuffle

    tickets = []
    for _ in range(ticket_count):
        shuffle(questions)
        ticket = f"Билет {_ + 1}:\n"
        ticket_questions = questions[:questions_per_ticket]
        ticket += "\n".join(f"{i + 1}. {question}" for i, question in enumerate(ticket_questions))
        tickets.append(ticket)
    return tickets

def extract_subject_code_from_url(url):
    return url.split('/')[-1]

async def fetch_questions_from_api(subject):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://localhost:8000/questions/{subject}") as response:
            if response.status == 200:
                data = await response.json()
                return data.get("questions", [])
            else:
                logging.error(f"Ошибка при получении вопросов из API: {response.status}")
                return []

