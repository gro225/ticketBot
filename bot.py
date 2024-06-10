import asyncio
import logging
import uvicorn
from dispatcher import dp, bot
from database import on_startup, on_shutdown
from fastapi import FastAPI
import handlers.auth_handlers
import handlers.question_handlers

fastapi_app = FastAPI()

@fastapi_app.get("/")
async def read_root():
    return {"message": "success"}

@fastapi_app.get("/questions/{subject}")
async def get_questions(subject: str):
    logging.info(f"Получение вопросов для subject_code: {subject}")
    from database import db_pool
    async with db_pool.acquire() as connection:
        questions = await connection.fetch("SELECT question FROM questions WHERE subject = $1", subject)
        if not questions:
            logging.info(f"Вопросы не найдены для subject: {subject}")
            raise HTTPException(status_code=404, detail="Вопросы не найдены для данного предмета.")
        logging.info(f"Найдено {len(questions)} вопросов для subject: {subject}")
        return {"questions": [q["question"] for q in questions]}

async def start_fastapi():
    config = uvicorn.Config("bot:fastapi_app", host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

async def main():
    logging.basicConfig(level=logging.INFO)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    loop = asyncio.get_event_loop()
    loop.create_task(start_fastapi())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
