import os
from aiogram import Dispatcher, types, Router, Bot, F
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
import keyboards as kb
from  keyboards import Menu_Callback
from aiogram.types import Message, CallbackQuery
import logging
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import logging

from config import bot
from db.models import async_session
import db.requests as rq
from open_ai import get_movie_recommendation
from sqlalchemy.future import select
from kinopoisk_omdb import get_movies, extract_movie_data


#logging.basicConfig(level=logging.INFO)  # Настройка логирования, чтобы выводить все сообщения от уровня INFO и выше
logging.basicConfig(level=logging.DEBUG)  # Установите уровень DEBUG для отладки
logger = logging.getLogger(__name__)
router = Router()
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
class Anketa(StatesGroup):
    q1 = State()
    q2 = State()
    q3 = State()
    q4= State()
    q5 = State()
    q6 = State()
    q7 = State()

@router.message(F.text == 'Давай')
async def registration_start(message: Message, state: FSMContext) -> None:
    await message.answer(questions[0])
    await state.set_state(Anketa.q1)

@router.message(Anketa.q1)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q1=message.text)
    await message.answer(questions[1])
    await state.set_state(Anketa.q2)

@router.message(Anketa.q2)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q2=message.text)
    await message.answer(questions[2])
    await state.set_state(Anketa.q3)

@router.message(Anketa.q3)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q3=message.text)
    await message.answer(questions[3])
    await state.set_state(Anketa.q4)

@router.message(Anketa.q4)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q4=message.text)
    await message.answer(questions[4])
    await state.set_state(Anketa.q5)

@router.message(Anketa.q5)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q5=message.text)
    await message.answer(questions[5])
    await state.set_state(Anketa.q6)

@router.message(Anketa.q6)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q6=message.text)
    await message.answer(questions[6])
    await state.set_state(Anketa.q7)

@router.message(Anketa.q7)
async def set_q1(message: Message, state: FSMContext) -> None:
    await state.update_data(q7=message.text)
    user_data = await state.get_data()
    member = await bot.get_chat_member(chat_id='-100' + os.getenv("TEST_CHAT_ID"), user_id=message.from_user.id)
    await rq.check_and_add_recommendations(rec1 = user_data['q1'], rec2 = user_data['q2'], rec3 = user_data['q3'], rec4 = user_data['q4'],
                                      rec5 = user_data['q5'], rec6 = user_data['q6'], rec7 = user_data['q7'], user_id=message.from_user.id, async_session=async_session)

    await message.answer('Уфф...Все ответы записал.')
    await message.answer('Я смотрю, что ты опытный киноман, но даже тебя я смогу удивить.\n')
    if member.status == 'left':
        await message.answer('«Начинаю поиск фильмов. Пока что ты можешь подписаться на телеграм канал Вика про кино', reply_markup=kb.subscribe_button)
    else:
        await message.answer('Начинаю рекомендовать фильмы!')
    await state.clear()





@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)

    await message.answer(
        "Привет! Добро пожаловать в кино-бот!"

    )
    await message.answer(
        'Этот бот.... (объснение функционала)',
        reply_markup=kb.main_menu_button
    )




@router.callback_query(F.data == 'check')
async def check_sub(callback : CallbackQuery, bot: Bot ):
    is_subscribed = await bot.get_chat_member(chat_id = '-100' + os.getenv("TEST_CHAT_ID"), user_id=callback.from_user.id)
    logging.info(f"Статус пользователя: {is_subscribed.status}")
    if is_subscribed.status != 'left':
        await callback.message.answer(
            "Спасибо за подписку!\nНачинаю рекомендовать фильмы!",
            reply_markup=kb.main_menu_button  # Показать основное меню
        )
    else:
        await callback.message.answer(
            "Для начала подпишитесь на наш канал, чтобы продолжить.",
            reply_markup=kb.subscribe_button  # Показываем кнопку для подписки
        )
    await callback.answer()

@router.message(F.text == 'Мой Профиль')
async def my_profile(message: types.Message):
    await message.answer('Прежде, чем порекомендовать тебе фильм, мне нужно узнать о тебе больше информации.\n'
                         'Сейчас я задам тебе 7 вопросов, а тебе нужно будет на них ответить. Чем развёртаннее будут'
                         ' твои ответы, тем лучше я смогу настроить свой рекомендательный алгоритм\nПриступим?',
                         reply_markup = kb.set_profile_button)


@router.message(F.text == 'Рекомендации')
async def get_recommendations(message: types.Message,  state: FSMContext):
    response = await get_movie_recommendation(message.from_user.id)
    movies_data = await get_movies(response)  # Не забываем await
    movies = await extract_movie_data(movies_data)
    await state.update_data(movies=movies)
    logger.debug(f"Movies list 1: {movies}")

    # Отображаем первый фильм
    current_index = 0
    movie = movies[current_index]



    poster_url = movie['poster']
    movie_text = (
        f"**Название:** {movie['title']}\n"
        f"**Год:** {movie['year']}\n"
        f"**Рейтинг:** {movie['rating']}\n"
        f"**Длительность:** {movie['duration']}\n"
        f"**Жанры:** {movie['genres']}\n\n"
        f"**Описание:** {movie['description']}"
        f"ID: {movie['movie_id']}"
    )
    keyboard = kb.user_recommendation_button(current_index)
    if poster_url and poster_url != 'No image available':
        await message.answer_photo(photo=poster_url, caption=movie_text, reply_markup=keyboard)
    else:
        await message.answer(movie_text, reply_markup=keyboard)

@router.callback_query(Menu_Callback.filter())
async def handle_movie_action(callback: types.CallbackQuery, callback_data: Menu_Callback, state: FSMContext):
    # Получаем список фильмов и текущий индекс
    data = await state.get_data()
    movies = data.get("movies", [])
    current_index = callback_data.index

    # Обрабатываем действие пользователяЫ
    action = callback_data.menu_name
    movie = movies[current_index]  # Определяем movie перед использованием
    logger.debug(f"Data from FSMContext: {data}")
    logger.debug(f"Movies list: {movies}")
    logger.debug(f"Current movie: {movie}")

    if action == "like":
        await callback.message.answer(f"ID фильма: {movie['movie_id']}")

        #await rq.add_to_likes(callback.from_user.id, movie['movie_id'])
    elif action == "next":
        await rq.add_to_next(callback.from_user.id, movie['movie_id'])

    # Переход к следующему фильму
    current_index += 1
    if current_index >= len(movies):
        await callback.message.answer("Подожди немного, сейчас мы найдем еще фильмы :)")
        await callback.answer()
        return

    # Отображение следующего фильма
    movie = movies[current_index]
    poster_url = movie['poster']
    movie_text = (
        f"**Название:** {movie['title']}\n"
        f"**Год:** {movie['year']}\n"
        f"**Рейтинг:** {movie['rating']}\n"
        f"**Длительность:** {movie['duration']}\n"
        f"**Жанры:** {movie['genres']}\n\n"
        f"**Описание:** {movie['description']}"
    )

    # Генерируем новую клавиатуру с обновленным индексом
    keyboard = kb.user_recommendation_button(current_index)

    if poster_url and poster_url != 'No image available':
        await callback.message.edit_media(
            media=types.InputMediaPhoto(media=poster_url, caption=movie_text),
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(movie_text, reply_markup=keyboard)

    # Сохраняем текущий индекс в состоянии
    await state.update_data(current_index=current_index)

    # Уведомляем Telegram, что callback обработан
    await callback.answer()







@router.message(F.text == 'На главную')
async def go_to_main_page(message: types.Message):
    await message.answer(
        "Выберите пункт из меню",
        reply_markup=kb.main_menu_button
    )