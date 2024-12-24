import aiohttp
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

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


async def find_in_ombd(movie_list):
    movie_imdb_ids = {}
    tasks = []  # Список задач для асинхронных запросов

    # Формируем задачи для асинхронных запросов
    for movie in movie_list:
        tasks.append(get_imdb_id(movie))

    # Выполняем все задачи одновременно
    imdb_ids = await asyncio.gather(*tasks)

    # Сохраняем результаты
    for i, movie in enumerate(movie_list):
        imdb_id = imdb_ids[i]
        if imdb_id:
            movie_imdb_ids[movie] = imdb_id
        else:
            movie_imdb_ids[movie] = 'Not Found'

    return movie_imdb_ids


async def find_in_kinopoisk_by_imdb(movie_imdb_ids):
    movies_data = {}  # Словарь для хранения данных о фильмах из КиноПоиска

    # Перебираем IMDb ID и делаем запрос для каждого фильма
    tasks = []
    for movie, imdb_id in movie_imdb_ids.items():
        if imdb_id != 'Not Found':
            url = f'https://api.kinopoisk.dev/v1.4/movie?externalId.imdb={imdb_id}&token={API_KEY_KINOPOISK}'
            tasks.append(fetch_movie_data(url, movie))  # Передаем URL и название фильма

    # Выполняем все запросы одновременно
    movie_data = await asyncio.gather(*tasks)

    # Сохраняем данные
    for data, (movie, imdb_id) in zip(movie_data, movie_imdb_ids.items()):
        if data:
            movies_data[movie] = {'imdb_id': imdb_id, 'data': data}
        else:
            movies_data[movie] = {'imdb_id': imdb_id, 'data': 'Not Found'}

    return movies_data


async def fetch_movie_data(url, movie_title):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"Ошибка запроса для {movie_title}: {response.status}")
                    return None
    except Exception as e:
        print(f"Ошибка при получении данных для {movie_title}: {e}")
        return None


async def get_movies(movies_list):
    movie_imdb_ids = await find_in_ombd(movies_list)
    movies_data = await find_in_kinopoisk_by_imdb(movie_imdb_ids)
    return movies_data



async def extract_movie_data(movies_data):
    movie_info_list = []  # List to store movie info
    for movie, data in movies_data.items():
        movie_id = data['imdb_id']
        movie_info = data['data']

        if movie_info != 'Not Found' and 'docs' in movie_info and movie_info['docs']:
            movie_info = movie_info['docs'][0]

            title_russian = movie_info.get('name', 'N/A')  # Название на русском
            year = movie_info.get('year', 'Unknown')  # Год выхода
            poster_url = movie_info.get('poster', {}).get('url', 'No image available')  # URL обложки
            description = movie_info.get('shortDescription', 'No description available')  # Описание
            rating = movie_info.get('rating', {}).get('kp', 'No rating available')  # Рейтинг на КиноПоиске

            # Извлечение жанров (преобразуем список словарей в строки)
            genres_list = movie_info.get('genres', [])
            genres = ', '.join([genre.get('name', 'Unknown') for genre in genres_list])

            duration = movie_info.get('movieLength', 'N/A')  # Длительность

            # Добавление данных в список
            movie_info_list.append({
                'movie_id': movie_id,
                'title': title_russian,
                'year': year,
                'poster': poster_url,
                'description': description,
                'rating': rating,
                'genres': genres,
                'duration': f"{duration} min" if isinstance(duration, int) else duration,
            })
        else:
            # Если данные о фильме не найдены
            movie_info_list.append({
                'movie_id': movie_id,
                'title': movie,
                'year': 'Not Found',
                'poster': 'No image available',
                'description': 'Not Found',
                'rating': 'Not Found',
                'genres': 'Not Found',
                'duration': 'Not Found',
            })

    return movie_info_list



