import aiohttp
import os
import asyncio
from dotenv import load_dotenv

from src.db.requests import get_liked_movies, get_disliked_movies

load_dotenv()

import logging
# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_KEY_OMDB = os.getenv('OMDB_API_KEY')
API_KEY_KINOPOISK = os.getenv('KINOPOISK_API_KEY')


async def get_imdb_id(movie_title):
    url = f'http://www.omdbapi.com/?t={movie_title}&apikey={API_KEY_OMDB}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()

                if data['Response'] == 'True':
                    return data['imdbID']
                else:
                    return None
    except Exception as e:
        print(f"Error fetching IMDb ID for {movie_title}: {e}")
        return None


async def find_in_ombd(movie_list, user_id):
    movie_imdb_ids = {}
    tasks = []

    # Предварительно загружаем предпочтения пользователя
    liked_movies = await get_liked_movies(user_id)
    disliked_movies = await get_disliked_movies(user_id)

    # Формируем задачи для асинхронных запросов
    for movie in movie_list:
        tasks.append(get_imdb_id(movie))

    # Выполняем все задачи одновременно
    imdb_ids = await asyncio.gather(*tasks)

    # Сохраняем результаты
    for i, movie in enumerate(movie_list):
        imdb_id = imdb_ids[i]
        if not imdb_id or imdb_id in liked_movies or imdb_id in disliked_movies:
            continue
        movie_imdb_ids[movie] = imdb_id if imdb_id else 'Not Found'

    logger.info(f"Movie IMDb IDs: {movie_imdb_ids}")
    return movie_imdb_ids




async def fetch_movie_data(url, movie_title, session):
    try:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                logger.error(f"Ошибка запроса для {movie_title}: {response.status}")
                return None
    except Exception as e:
        logger.error(f"Ошибка при получении данных для {movie_title}: {e}")
        return None


async def find_in_kinopoisk_by_imdb(movie_imdb_ids):
    movies_data = {}
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_movie_data(
                f'https://api.kinopoisk.dev/v1.4/movie?externalId.imdb={imdb_id}&token={API_KEY_KINOPOISK}',
                movie,
                session
            )
            for movie, imdb_id in movie_imdb_ids.items() if imdb_id != 'Not Found'
        ]
        movie_data = await asyncio.gather(*tasks)

    for data, (movie, imdb_id) in zip(movie_data, movie_imdb_ids.items()):
        movies_data[movie] = {'imdb_id': imdb_id, 'data': data or 'Not Found'}
    logger.info(f"Movies data from Kinopoisk: {movies_data}")
    return movies_data



async def get_movies(movies_list, user_id):
    movie_imdb_ids = await find_in_ombd(movies_list, user_id)
    movies_data = await find_in_kinopoisk_by_imdb(movie_imdb_ids)
    return movies_data



async def extract_movie_data(movies_data):

    movie_info_list = []  # List to store movie info
    for movie, data in movies_data.items():
        movie_info = (data['data'].get('docs', [{}])[0]
                      if data['data'] != 'Not Found' else None)

        if movie_info:
            # Извлечение данных из movie_info
            title_russian = movie_info.get('name', 'N/A')  # Название на русском
            year = movie_info.get('year', 'Unknown')  # Год выхода
            poster_url = movie_info.get('poster', {}).get('url', 'No image available')  # URL постера
            description = (
                    movie_info.get('shortDescription') or
                    movie_info.get('description') or
                    'No description available'
            )
            rating = movie_info.get('rating', {}).get('kp', 'No rating available')  # Рейтинг Кинопоиска

            # Извлечение жанров и преобразование в строку
            genres_list = movie_info.get('genres', [])
            genres = ', '.join([genre.get('name', 'Unknown') for genre in genres_list])

            # Длительность фильма
            duration = movie_info.get('movieLength', 'N/A')
            duration_text = f"{duration} min" if isinstance(duration, int) else duration

            # Добавление в список
            movie_info_list.append({
                'movie_id': data['imdb_id'],
                'title': title_russian,
                'year': year,
                'poster': poster_url,
                'description': description,
                'rating': rating,
                'genres': genres,
                'duration': duration_text,
            })
        else:
            # Если данные о фильме не найдены
            movie_info_list.append({
                'movie_id': data['imdb_id'],
                'title': movie,
                'year': 'Not Found',
                'poster': 'No image available',
                'description': 'Not Found',
                'rating': 'Not Found',
                'genres': 'Not Found',
                'duration': 'Not Found',
            })

    logger.info(f"Extracted movie data: {movie_info_list}")

    return movie_info_list


async def get_favourites_data(imdb_ids):
    """
    Получение и подготовка данных для избранных фильмов.
    """
    favourites_data = []
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_movie_data(
                f'https://api.kinopoisk.dev/v1.4/movie?externalId.imdb={imdb_id}&token={API_KEY_KINOPOISK}',
                imdb_id,  # IMDb ID
                session
            )
            for imdb_id in imdb_ids
        ]
        # Выполняем все запросы параллельно
        movies_data = await asyncio.gather(*tasks)

    # Обрабатываем результаты запросов
    for imdb_id, data in zip(imdb_ids, movies_data):
        favourites_data.append({
            "imdb_id": imdb_id,
            "title": data.get("name", "Неизвестно"),
            "year": data.get("year", "Неизвестно"),
            "rating": data.get("rating", {}).get("kp", "N/A"),
            "poster": data.get("poster", {}).get("url", "No image available"),
            "description": data.get("description", "Описание отсутствует"),
            "genres": ", ".join([genre["name"] for genre in data.get("genres", [])]),
            "duration": f'{data.get("movieLength", 0)} мин'
        })
    return favourites_data


