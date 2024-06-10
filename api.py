import logging
from fastapi import FastAPI, HTTPException
from database import db_pool

app = FastAPI()

@app.get("/questions/{subject}")
async def get_questions(subject: str):
    logging.info(f"Получение вопросов для subject_code: {subject}")
    if db_pool is None:
        logging.error("db_pool не инициализирован")
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных.")
    async with db_pool.acquire() as connection:
        questions = await connection.fetch("SELECT question FROM questions WHERE subject = $1", subject)
        if not questions:
            logging.info(f"Вопросы не найдены для subject: {subject}")
            raise HTTPException(status_code=404, detail="Вопросы не найдены для данного предмета.")
        logging.info(f"Найдено {len(questions)} вопросов для subject: {subject}")
        return {"questions": [q["question"] for q in questions]}
