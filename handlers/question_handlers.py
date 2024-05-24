from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.filters import Text
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dispatcher import dp, db_pool, bot
from auth_handlers import check_user_exists, check_teacher_exists

# Кнопки
def get_confirmation_keyboard():
    buttons = [
        [KeyboardButton(text="Да"), KeyboardButton(text="Нет")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def generate_tickets(questions, ticket_count):
    from random import shuffle

    tickets = []
    questions_per_ticket = len(questions) // ticket_count
    for _ in range(ticket_count):
        shuffle(questions)
        ticket = "\n".join(questions[:questions_per_ticket])
        tickets.append(ticket)
    return tickets

# Обработчик команды /add_questions
@dp.message(Command("add_questions"))
async def start_adding_questions(message: types.Message, state: FSMContext):
    user_data = await check_user_exists(message.from_user.id)
    teacher_data = await check_teacher_exists(user_data['id'])

    if teacher_data:
        await message.answer("Введите вопрос:")
        await state.set_state("awaiting_question")
        await state.update_data(questions=[])
    else:
        await message.answer("У вас нет прав на выполнение этой команды.")

@dp.message(state="awaiting_question")
async def process_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get('questions', [])
    questions.append(message.text)
    await state.update_data(questions=questions)
    await message.answer("Вопрос добавлен. Хотите добавить еще один?", reply_markup = get_confirmation_keyboard())
    await state.set_state("confirm_more_questions")

@dp.message(state="confirm_more_questions")
async def confirm_more_questions(message: types.Message, state: FSMContext):
    if message.text.lower() == "да":
        await message.answer("Введите следующий вопрос:")
        await state.set_state("awaiting_question")
    elif message.text.lower() == "нет":
        await message.answer("Сколько билетов нужно сгенерировать?")
        await state.set_state("awaiting_ticket_count")
    else:
        await message.answer("Пожалуйста, используйте кнопки для ответа.", reply_markup=get_confirmation_keyboard())

@dp.message(state="awaiting_ticket_count")
async def process_ticket_count(message: types.Message, state: FSMContext):
    try:
        ticket_count = int(message.text)
        data = await state.get_data()
        questions = data.get('questions', [])
        user_data = await check_user_exists(message.from_user.id)
        teacher_data = await check_teacher_exists(user_data['id'])
        groups = teacher_data['groups']

        async with db_pool.acquire() as connection:
            for group in groups:
                students = await connection.fetch("SELECT tg_id FROM students WHERE group = $1", group)
                tickets = generate_tickets(questions, ticket_count)
                for student in students:
                    for ticket in tickets:
                        await bot.send_message(student['tg_id'], ticket)

        await message.answer("Билеты успешно сгенерированы и отправлены студентам.")
        await state.finish()

    except ValueError:
        await message.answer("Пожалуйста, введите корректное число.")

