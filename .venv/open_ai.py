from openai import AsyncOpenAI
from dotenv import load_dotenv
from db.models import async_session
from db.models import RecommendationSettings

import os
import ast
from sqlalchemy.future import select

# Список вопросов для настройки профиля
questions = [
    "Какие жанры фильмов тебе больше всего заходят?",
    "Есть ли фильм, который ты готов пересматривать бесконечно? Какой это?",
    "Какие актеры или режиссеры тебя реально цепляют?",
    "Ты больше любишь фильмы с напряжённым сюжетом или расслабляющие?",
    "Любишь фильмы с открытым финалом или завершённым?",
    "Может, у тебя есть любимые фильмы из какой-то страны?",
    "Какой фильм ты выберешь на вечер после тяжёлого дня?"
]

load_dotenv()
client = AsyncOpenAI(api_key=os.getenv('CHATGPT_API_KEY'))

async def get_movie_recommendation(user_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(RecommendationSettings).where(RecommendationSettings.user_id == user_id)
            )
            recommendation = result.scalars().first()
            #Возвращаем словарь с ответами пользователя
            if recommendation:
                answers = {
                    "rec1": recommendation.rec1,
                    "rec2": recommendation.rec2,
                    "rec3": recommendation.rec3,
                    "rec4": recommendation.rec4,
                    "rec5": recommendation.rec5,
                    "rec6": recommendation.rec6,
                    "rec7": recommendation.rec7,
                }

    text = 'Я ответил на вопросы о фильмах. Порекомендуй мне фильмы.\n'
    for i, question in enumerate(questions):
        answer_key = f"rec{i + 1}"  # Ключи словаря rec1, rec2 и т. д.
        answer = answers.get(answer_key, "Ответ отсутствует")  # Берем ответ или пишем "Ответ отсутствует"
        text += f"Вопрос {i + 1}: {question}\nОтвет: {answer}\n\n"



    response = await client.chat.completions.create(
        messages = [{
        "role": "system",
            "content": (
                "You are a recommendation system for selecting movies based on the user's preferences. "
                    "Your task is to recommend movies for the user based on their preferences. "
                    "Output 3 movies that match the user's preferences. Below are the user's answers to the preference questions in Russian, "
                    "however, all movie titles you recommend should strictly be in English. The output data should be in the format of a Python list Movies = [], "
                    "containing only the movie titles in English"
            )

        },
      {
        "role": "user",
        "content": str(text)
      }],
        model='gpt-4o-mini-2024-07-18'
    )

    movie_list_str = response.choices[0].message.content
    movie_list = movie_list_str.replace('Movies = [', '').replace(']', '').replace('"', '').split(
        ',')  # Обработка строки
    movie_list = [movie.strip() for movie in movie_list]  # Убираем лишние пробелы
    return movie_list








