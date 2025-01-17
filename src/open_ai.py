from openai import AsyncOpenAI
from dotenv import load_dotenv
from db.models import async_session
from db.models import RecommendationSettings, UserPreferences
from kinopoisk_omdb import find_by_imdb


import os
from sqlalchemy.future import select
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

            # Инициализация словаря с ответами пользователя
            answers = {
                "rec1": "Ответ отсутствует",
                "rec2": "Ответ отсутствует",
                "rec3": "Ответ отсутствует",
                "rec4": "Ответ отсутствует",
                "rec5": "Ответ отсутствует",
                "rec6": "Ответ отсутствует",
                "rec7": "Ответ отсутствует",
            }

            # Если рекомендации найдены, обновляем ответы
            if recommendation:
                answers.update({
                    "rec1": recommendation.rec1 or "Ответ отсутствует",
                    "rec2": recommendation.rec2 or "Ответ отсутствует",
                    "rec3": recommendation.rec3 or "Ответ отсутствует",
                    "rec4": recommendation.rec4 or "Ответ отсутствует",
                    "rec5": recommendation.rec5 or "Ответ отсутствует",
                    "rec6": recommendation.rec6 or "Ответ отсутствует",
                    "rec7": recommendation.rec7 or "Ответ отсутствует",
                })

    # Формирование текста для GPT
    text = 'Я ответил на вопросы о фильмах. Порекомендуй мне фильмы.\n'
    for i, question in enumerate(questions):
        answer_key = f"rec{i + 1}"  # Ключи словаря rec1, rec2 и т. д.
        answer = answers.get(answer_key, "Ответ отсутствует")  # Берем ответ или пишем "Ответ отсутствует"
        text += f"Вопрос {i + 1}: {question}\nОтвет: {answer}\n\n"

    # Отправка запроса в OpenAI
    response = await client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a recommendation system for selecting movies based on the user's preferences. "
                    "Your task is to recommend movies for the user based on their preferences. "
                    "Output 5 movies that match the user's preferences. Below are the user's answers to the preference questions in Russian, "
                    "however, all movie titles you recommend should strictly be in English. The output data should be in the format of a Python list Movies = [], "
                    "containing only the movie titles in English."
                )
            },
            {
                "role": "user",
                "content": str(text)
            }
        ],
        model='gpt-4o-mini-2024-07-18'
    )

    # Обработка ответа GPT
    movie_list_str = response.choices[0].message.content
    pattern = r"Movies = \[\s*(.*?)\s*\]"
    match = re.search(pattern, movie_list_str, re.DOTALL)
    movie_list = []
    if match:
        movies_string = match.group(1)
        movie_list = [movie.strip().strip('"').strip("'") for movie in re.split(r',\s*', movies_string)]

    logger.info(f"Extracted CHAT GPT data: {movie_list_str}")
    logger.info(f"movie_list: {movie_list}, {type(movie_list)}")

    return movie_list




async def movie_rec(user_id: int):
    async with async_session() as session:
        async with session.begin():
            res = await session.execute(
                select(UserPreferences).where(UserPreferences.user_id == user_id)
            )
            preferences = res.scalars()
            watched_movies = [pref.watched for pref in preferences if pref.watched]
            liked_movies = [pref.rec_like for pref in preferences if pref.rec_like]


            logger.info(preferences)

            logger.info("WATCHED LIKED")
            logger.info(watched_movies)
            logger.info(liked_movies)

    if len(watched_movies) >= 5 or len(liked_movies) >= 5:
        logger.info("У пользователя есть понравившиеся фильмы")

        watched_movies = watched_movies[-5:]
        liked_movies = liked_movies[-5:]
        # Логирование для проверки
        logger.info(f"Last 5 watched movies: {watched_movies}")
        logger.info(f"Last 5 liked movies: {liked_movies}")

        movies_1 = await find_by_imdb(watched_movies)  # Передаем список
        logger.info(movies_1)
        movies_2 = await find_by_imdb(liked_movies)  # Передаем список
        logger.info(movies_2)
        data = {**movies_1, **movies_2}  # Объединяем два словаря
        movies = [
            item["data"]["docs"][0]  # Первый фильм из списка документов
            for item in data.values() if item["data"]["docs"]
        ]


        movie_names = ', '.join([movie.get('name', 'Unknown') for movie in movies])
        text = f"Here are the movies that the user liked: {movie_names}"

        response = await client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a recommendation system for selecting movies based on the user's preferences. "
                        "Your task is to recommend movies for the user based on their preferences. "
                        "Output 5 movies that match the user's preferences. Below are the user's answers to the preference questions in Russian, "
                        "however, all movie titles you recommend should strictly be in English. The output data should be in the format of a Python list Movies = [], "
                        "containing only the movie titles in English."
                    )
                },
                {
                    "role": "user",
                    "content": str(text)
                }
            ],
            model='gpt-4o-mini-2024-07-18'
        )
        logger.debug(f"Response from movie_rec: {response}")


        # Обработка ответа GPT
        movie_list_str = response.choices[0].message.content
        pattern = r"Movies = \[\s*(.*?)\s*\]"
        match = re.search(pattern, movie_list_str, re.DOTALL)
        movie_list = []
        if match:
            movies_string = match.group(1)
            movie_list = [movie.strip().strip('"').strip("'") for movie in re.split(r',\s*', movies_string)]
            return movie_list

        else:
            logger.error("Pattern not found in GPT response. Response: %s", movie_list_str)
        logger.info(f"Extracted CHAT GPT data: {movie_list_str}")
        logger.info(f"movie_list: {movie_list}, {type(movie_list)}")

        if not movie_list:
            logger.error("movie_list is None or empty")
            logger.info(movie_list)
            return []


    else:
        logger.info("\nВызываем обычные рекомендации\n")
        return await get_movie_recommendation(user_id=user_id)











