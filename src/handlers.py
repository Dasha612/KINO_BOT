import os
from aiogram import types, Router, Bot, F
from aiogram.filters import CommandStart, Command
import keyboards as kb
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import logging

from config import bot
from db.models import async_session
import db.requests as rq
from open_ai import movie_rec, get_movie_recommendation
from kinopoisk_omdb import get_movies, extract_movie_data, find_by_imdb
from src.callback_data import Menu_Callback


logging.basicConfig(level=logging.INFO)
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



@router.callback_query(F.data == "set_profile")
async def registration_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(questions[0])
    await state.set_state(Anketa.q1)
    await callback.answer()

@router.message(Anketa.q1)
async def set_q1(message: types.Message, state: FSMContext):
    await state.update_data(q1=message.text)
    await message.answer(questions[1])
    await state.set_state(Anketa.q2)

@router.message(Anketa.q2)
async def set_q2(message: types.Message, state: FSMContext):
    await state.update_data(q2=message.text)
    await message.answer(questions[2])
    await state.set_state(Anketa.q3)

@router.message(Anketa.q3)
async def set_q3(message: types.Message, state: FSMContext):
    await state.update_data(q3=message.text)
    await message.answer(questions[3])
    await state.set_state(Anketa.q4)

@router.message(Anketa.q4)
async def set_q4(message: types.Message, state: FSMContext):
    await state.update_data(q4=message.text)
    await message.answer(questions[4])
    await state.set_state(Anketa.q5)

@router.message(Anketa.q5)
async def set_q5(message: types.Message, state: FSMContext):
    await state.update_data(q5=message.text)
    await message.answer(questions[5])
    await state.set_state(Anketa.q6)

@router.message(Anketa.q6)
async def set_q6(message: types.Message, state: FSMContext):
    await state.update_data(q6=message.text)
    await message.answer(questions[6])
    await state.set_state(Anketa.q7)

@router.message(Anketa.q7)
async def set_q7(message: types.Message, state: FSMContext):
    await state.update_data(q7=message.text)
    user_data = await state.get_data()
    member = await bot.get_chat_member(chat_id='-100' + os.getenv("TEST_CHAT_ID"), user_id=message.from_user.id)

    # Сохраняем рекомендации
    await rq.check_and_add_recommendations(
        rec1=user_data['q1'], rec2=user_data['q2'], rec3=user_data['q3'],
        rec4=user_data['q4'], rec5=user_data['q5'], rec6=user_data['q6'], rec7=user_data['q7'],
        user_id=message.from_user.id, async_session=async_session
    )
    await rq.update_status(message.from_user.id, True )

    await message.answer('Уфф...Все ответы записал.')
    await message.answer('Я смотрю, что ты опытный киноман, но даже тебя я смогу удивить.', reply_markup=types.ReplyKeyboardRemove())

    if member.status == 'left':
        await message.answer(
            'Начинаю поиск фильмов. Пока что ты можешь подписаться на телеграм канал Вика про кино',
            reply_markup=kb.subscribe_button
        )
    else:
        await message.answer('Начинаю рекомендовать фильмы!')
        response = await movie_rec(message.from_user.id)
        movies_data = await get_movies(response, message.from_user.id)
        movies = await extract_movie_data(movies_data)
        await state.update_data(movies=movies, current_index=0)

        # Отображаем первый фильм
        await send_movie_or_edit(message, movies[0], state, 0, message.from_user.id)

    await state.update_data(current_index=0)

@router.message(CommandStart())
async def cmd_start(message: Message):
    await rq.set_user(message.from_user.id)

    await message.answer(
        "Привет! Добро пожаловать в кино-бот!"

    )
    await message.answer(
        'Этот бот.... (объяснение функционала)',
        reply_markup=kb.main_menu_button
    )

@router.callback_query(F.data == 'check')
async def check_sub(callback: CallbackQuery, bot: Bot, state: FSMContext):
    is_subscribed = await bot.get_chat_member(chat_id='-100' + os.getenv("TEST_CHAT_ID"), user_id=callback.from_user.id)

    if is_subscribed.status != 'left':
        # Благодарим за подписку
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        await callback.message.answer(
            "Спасибо за подписку!\nНачинаю рекомендовать фильмы!"
        )

        # Логика для начала рекомендаций
        response = await movie_rec(callback.from_user.id)
        movies_data = await get_movies(response, callback.from_user.id)
        movies = await extract_movie_data(movies_data)
        await state.update_data(movies=movies, current_index=0)

        # Отображаем первый фильм
        await send_movie_or_edit(callback.message, movies[0], state, 0, user_id=callback.from_user.id)
    else:
        # Если пользователь не подписан, напомнить подписаться
        await callback.message.answer(
            "Для начала подпишитесь на наш канал, чтобы продолжить.",
            reply_markup=kb.subscribe_button  # Показываем кнопку для подписки
        )

    await callback.answer()


@router.callback_query(F.data == 'my_profile')
async def my_profile(callback: CallbackQuery):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    user_id = callback.from_user.id
    status = await rq.get_status(user_id)
    status = 'настроены' if status else 'не настроены'

    await callback.message.answer(
        (
            f"<b>👤 Ваш профиль:</b>\n"
            f"<b>ID:</b> <code>{user_id}</code>\n"
            #f"<b>Статус подписки:</b> <i>отключена</i>\n"
            f"<b>Рекомендации:</b> <i>{status}</i>"
        ),
        parse_mode="HTML",  # Используем HTML для форматирования
        reply_markup=kb.profile_menu_buttons
    )


@router.callback_query(F.data == 'recommendations')
async def get_recommendations(callback: CallbackQuery, state: FSMContext):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    user_id = callback.from_user.id
    #start_rec_message = await callback.message.answer("Запускаю рекомендации...", reply_markup=ReplyKeyboardRemove())
    member = await bot.get_chat_member(
        chat_id='-100' + os.getenv("TEST_CHAT_ID"),
        user_id=user_id
    )

    if member.status == 'left':  # Пользователь не подписан
        await callback.message.answer(
            "Для того чтобы продолжить и получить рекомендации, подпишитесь на наш телеграм-канал Вика про кино.",
            reply_markup=kb.subscribe_button
        )
        return

    unwatched_movies = await rq.get_unrec(user_id)
    logger.info(f"UNWATCHED for user id {user_id}: {unwatched_movies}")

    recommendations = await rq.get_rec(user_id)
    if len(unwatched_movies) != 0:
        res = await find_by_imdb(unwatched_movies)
        #await start_rec_message.delete()
        movies = [
            {**movie, "from_unwatched": True}  # Добавляем флаг
            for movie in await extract_movie_data(res)
        ]
        await state.update_data(movies=movies, current_index=0)

        # Отображаем первый фильм
        await send_movie_or_edit(callback.message, movies[0], state, 0, user_id)
        return

    if not recommendations:
        await callback.message.answer(
            "Прежде чем порекомендовать тебе фильм, мне нужно узнать о тебе больше информации.\n"
            "Сейчас я задам тебе 7 вопросов, а тебе нужно будет на них ответить. Чем развёрнутее будут "
            "твои ответы, тем лучше я смогу настроить свой рекомендательный алгоритм.\nПриступим?",
            reply_markup=kb.set_profile_button,
        )
        #await start_rec_message.delete()
        return


    response = await movie_rec(user_id)
    movies_data = await get_movies(response, user_id)

    movies = await extract_movie_data(movies_data)
    logger.info(f"Фильмы для показа: {movies}")

    await state.update_data(movies=movies, current_index=0)
    #await start_rec_message.delete()

    # Отображаем первый фильм
    await send_movie_or_edit(callback.message, movies[0], state, 0, user_id)


async def send_movie_or_edit(message, movie, state, index, user_id):
    title = movie['title']
    google_search_url = f"https://www.google.com/search?q=смотреть+фильм+{title.replace(' ', '+')}"

    poster_url = movie.get('poster', 'No image available')
    if not poster_url or poster_url == 'No image available':
        poster_url = None  # Устанавливаем None, если изображение отсутствует
    rating = round(float(movie['rating']), 1) if movie['rating'] != 'Not Found' else 'Not Found'

    movie_text = (
        f"<b>Название:</b> {title}\n"
        f"<b>Год:</b> {movie['year']}\n"
        f"<b>Рейтинг:</b> {rating}\n"
        f"<b>Длительность:</b> {movie['duration']}\n"
        f"<b>Жанры:</b> {movie['genres']}\n\n"
        f"<b>Описание:</b> {movie['description']}\n"
        f'<a href="{google_search_url}">Смотреть</a>'
    )
    keyboard = kb.user_recommendation_button(index)

    # Получаем ID сообщения из состояния, если оно есть
    data = await state.get_data()
    message_id = data.get("message_id")

    # Если постер доступен
    if poster_url:
        try:
            if message_id:
                # Если сообщение существует, редактируем его
                await message.bot.edit_message_media(
                    chat_id=message.chat.id,
                    message_id=message_id,
                    media=InputMediaPhoto(
                        media=poster_url,
                        caption=movie_text,
                        parse_mode="HTML"
                    ),
                    reply_markup=keyboard
                )
            else:
                # Если сообщение ещё не существует, отправляем новое
                sent_message = await message.answer_photo(
                    photo=poster_url,
                    caption=movie_text,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                # Сохраняем ID сообщения
                await state.update_data(message_id=sent_message.message_id)
        except Exception as e:
            # Логируем ошибку и отправляем текст без изображения
            logger.error(f"Failed to send photo: {e}")
            await message.answer(
                text=movie_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    else:
        # Если постера нет, отправляем только текст
        if message_id:
            await message.bot.edit_message_text(
                text=movie_text,
                chat_id=message.chat.id,
                message_id=message_id,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            sent_message = await message.answer(
                text=movie_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            # Сохраняем ID сообщения
            await state.update_data(message_id=sent_message.message_id)
    if movie.get("from_unwatched"):
        try:
            await rq.remove_unrec(user_id, movie['movie_id'])

        except Exception as e:
            logger.error(f"Failed to remove movie {movie['movie_id']} from unwatched_movies for user {user_id}: {e}")


@router.callback_query(Menu_Callback.filter())
async def handle_movie_action(callback: types.CallbackQuery, callback_data: Menu_Callback, state: FSMContext):
    # Получаем список фильмов и текущий индекс
    data = await state.get_data()
    movies = data.get("movies", [])
    current_index = data.get("current_index", 0)
    user_id = callback.from_user.id

    # Проверяем корректность индекса
    if current_index >= len(movies) or current_index < 0:
        await callback.message.answer("Возникла ошибка с выбором фильма. Попробуйте снова.")
        await callback.answer()
        return

    # Обрабатываем действие пользователя
    action = callback_data.menu_name
    movie = movies[current_index]

    # Логируем выбранное действие для отладки
    logger.info(f"User {callback.from_user.id} selected action: {action}")

    if action == "like":
        await rq.add_to_likes(callback.from_user.id, movie['movie_id'])
    elif action == "next":
        await rq.add_to_next(callback.from_user.id, movie['movie_id'])
    elif action == "Стоп":
        # Обработка оставшихся фильмов
        await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
        remaining_movies = movies[current_index:]  # Фильмы, которые ещё не были показаны
        logger.info(remaining_movies)
        for movie in remaining_movies:
            await rq.add_to_unrec(user_id, movie['movie_id'])

        # Очистка состояния и завершение рекомендаций
        await state.clear()
        await callback.message.answer(
            "Рекомендации остановлены. Возвращайтесь, когда захотите!",
            reply_markup=kb.main_menu_button
        )
        await callback.answer()
        return
    elif action == "watched":
        await callback.message.answer("Пожалуйста, оцените фильм", reply_markup=kb.rate_buttons)
        await state.update_data(last_action="watched")
        await callback.answer()
        return

    last_action = data.get("last_action", "")
    if last_action == "watched":
        return

    # Увеличиваем индекс для показа следующего фильма
    current_index += 1

    # Проверяем, достигли ли конца списка
    if current_index >= len(movies):
        # Получаем новые рекомендации
        loading_message = await callback.message.answer("Подождите немного, подгружаем новые рекомендации...")
        logger.info(f"Достигли конца списка. Новые реки для: {callback.from_user.id}")
        response = await movie_rec(callback.from_user.id)
        logger.info(f"Достигли конца списка. Новые реки: {response}")
        movies_data = await get_movies(response, callback.from_user.id)
        logger.info(f"Полученная инфа: {movies_data}")
        new_movies = await extract_movie_data(movies_data)
        logger.info(new_movies)
        #Проблема: чатгпт рекомендует фильмы, которые уже есть в лайках из-за чего список получается пустым
        #Не работают кнопки перемотки страницы в избранных


        # Если новых фильмов нет, завершаем
        if not new_movies:
            await loading_message.delete()
            await callback.message.answer('Кажется, произошла ошибка :(\nПопробуйте нажать кнопку "Стоп" и возобновить рекомендации или обратитесь в поддержку - @Ddasmii')
            await callback.answer()
            return
        await loading_message.delete()

        # Добавляем новые фильмы в список
        movies.extend(new_movies)
        await state.update_data(movies=movies)

    # Обновляем индекс в состоянии
    await state.update_data(current_index=current_index)

    # Отправляем следующий фильм
    if current_index < len(movies):
        await send_movie_or_edit(callback.message, movies[current_index], state, current_index, user_id)

    # Завершаем callback
    await callback.answer()






@router.callback_query(F.data.in_(['1', '2', '3', '4', '5']))
async def handle_rating(callback: types.CallbackQuery, state: FSMContext):
    # Получаем оценку пользователя
    user_rating = int(callback.data)
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    movies = data.get("movies", [])
    movie = movies[current_index]
    user_id = callback.from_user.id

    if user_rating >=4:
        await rq.save_movie_rating(user_id=callback.from_user.id, movie_id=movie['movie_id'])

    await callback.message.delete()

    # Сбрасываем состояние last_action
    await state.update_data(last_action="")

    # Переход к следующему фильму
    current_index += 1
    if current_index >= len(movies):
        loading_message = await callback.message.answer("Подождите немного, подгружаем новые рекомендации...")
        # Загружаем новые фильмы
        response = await movie_rec(callback.from_user.id)
        movies_data = await get_movies(response, callback.from_user.id)
        new_movies = await extract_movie_data(movies_data)
        await loading_message.delete()
        movies.extend(new_movies)
        current_index = len(movies) - len(new_movies)  # Сбрасываем индекс на начало новых фильмов
        await state.update_data(movies=movies)

    # Обновляем индекс и отображаем следующий фильм
    await state.update_data(current_index=current_index)
    await send_movie_or_edit(callback.message, movies[current_index], state, current_index, user_id)
    await callback.answer()



@router.callback_query(F.data == 'profile_reset_recommendations')
async def reset_rec(callback: CallbackQuery):

    await rq.reset_recommendations(callback.from_user.id, async_session=async_session)
    await rq.update_status(callback.from_user.id, False)
    await callback.message.answer(
        "Рекомендации сброшены.",
        reply_markup=kb.main_menu_button
    )
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)


@router.callback_query(F.data == 'main')
async def go_to_main_page(callback: CallbackQuery):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    await callback.message.answer(
        "Выберите пункт из меню",
        reply_markup=kb.main_menu_button  # Обычная клавиатура
    )







@router.callback_query(F.data == 'favourites')
async def favourites(callback: CallbackQuery):
    await bot.delete_message(chat_id=callback.message.chat.id, message_id=callback.message.message_id)
    # Получаем список IMDb ID фильмов из "Избранного"
    liked = await rq.get_liked_movies(callback.from_user.id)
    movies_on_page = 15
    page = 1  # Начальная страница

    if not liked:
        await callback.message.answer("У вас пока нет избранных фильмов.", reply_markup=kb.main)

    logger.info(f"Избранные: {liked}")

    # Получаем данные о фильмах с помощью новой функции
    favourites_data = await find_by_imdb(liked)



    logger.info(favourites_data)

    # Преобразуем словарь в список фильмов
    movies = [
        item["data"]["docs"][0]  # Первый фильм из списка документов
        for item in favourites_data.values() if item["data"]["docs"]
    ]



    # Получаем данные для текущей страницы
    start = (page - 1) * movies_on_page
    end = page * movies_on_page
    movies_for_page = movies[start:end]

    # Формируем список фильмов с форматированием
    movie_list = []
    for i, movie in enumerate(movies_for_page, start=start + 1):
        title = movie.get('name') or movie.get('alternativeName') or "Название недоступно"
        year = movie.get('year', 'Неизвестно')
        rating = round(movie.get('rating', {}).get('kp', 0), 1)
        google_search_url = f"https://www.google.com/search?q=смотреть+фильм+{title.replace(' ', '+')}"

        movie_list.append(
            f"<b>{i}. 🎬 <a href='{google_search_url}'>{title}</a></b>\n"
            f"   📅 <i>{year} год</i>\n"
            f"   ⭐ <i>Рейтинг: {rating if rating > 0 else 'Нет данных'}</i>"
        )

    # Отправляем список фильмов
    if movie_list:
        movie_list_text = "<b>🌟 Ваши избранные фильмы:</b>\n\n" + "\n\n".join(movie_list)

        # Создаем кнопки пагинации
        total_pages = -(-len(movies) // movies_on_page)  # Вычисляем общее количество страниц
        pagination_buttons = []

        if page > 1:
            pagination_buttons.append(InlineKeyboardButton(text='⏮️ В начало', callback_data='page_1'))
            pagination_buttons.append(InlineKeyboardButton(text='◀️ Назад', callback_data=f'page_{page - 1}'))

        if page < total_pages:
            pagination_buttons.append(InlineKeyboardButton(text='▶️ Вперед', callback_data=f'page_{page + 1}'))
            pagination_buttons.append(InlineKeyboardButton(text='⏩ В конец', callback_data=f'page_{total_pages}'))

        pagination_markup = InlineKeyboardMarkup(inline_keyboard=[
            pagination_buttons,
            [InlineKeyboardButton(text='На главную', callback_data='main')]
        ])

        await callback.message.answer(movie_list_text, parse_mode="HTML", disable_web_page_preview=True, reply_markup=pagination_markup)









