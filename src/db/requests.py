from db.models import User, Subscriptions, UserPreferences, RecommendationSettings, UserLimits, async_session
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker

from datetime import datetime
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError

async def set_user(
    id,
    user_start_date=datetime.utcnow(),
    user_end_date=datetime.utcnow(),
    user_active=True,
    user_request_total=0,
    user_request=0,
):
    async with async_session() as session:
        async with session.begin():
            try:
                # Проверяем, существует ли пользователь
                user = await session.scalar(select(User).where(User.user_id == id))
                if user:
                    # Если пользователь уже существует, обновляем его данные
                    user.user_end_date = user_end_date
                    user.user_active = user_active
                    await session.commit()
                    return

                # Если пользователя нет, добавляем нового
                new_user = User(
                    user_id=id,
                    user_start_date=user_start_date,
                    user_end_date=user_end_date,
                    user_active=user_active,
                    user_request_total=user_request_total,
                    user_request=user_request,
                )
                session.add(new_user)
                await session.commit()
            except IntegrityError as e:

                await session.rollback()  # Откатываем транзакцию




async def check_and_add_recommendations(rec1, rec2, rec3, rec4, rec5, rec6, rec7, user_id, async_session: sessionmaker):
    async with async_session() as session:
        # Проверяем, есть ли уже настройки рекомендаций для этого пользователя
        result = await session.execute(select(RecommendationSettings).filter_by(user_id=user_id))
        recommendation_settings = result.scalars().first()

        # Заменяем None на пустую строку
        rec1 = rec1 or ""
        rec2 = rec2 or ""
        rec3 = rec3 or ""
        rec4 = rec4 or ""
        rec5 = rec5 or ""
        rec6 = rec6 or ""
        rec7 = rec7 or ""

        # Если запись существует, обновляем только пустые поля
        if recommendation_settings:
            if not recommendation_settings.rec1:
                recommendation_settings.rec1 = rec1
            if not recommendation_settings.rec2:
                recommendation_settings.rec2 = rec2
            if not recommendation_settings.rec3:
                recommendation_settings.rec3 = rec3
            if not recommendation_settings.rec4:
                recommendation_settings.rec4 = rec4
            if not recommendation_settings.rec5:
                recommendation_settings.rec5 = rec5
            if not recommendation_settings.rec6:
                recommendation_settings.rec6 = rec6
            if not recommendation_settings.rec7:
                recommendation_settings.rec7 = rec7

            await session.commit()

        else:
            # Если все поля пусты, ничего не делаем
            if not any([rec1, rec2, rec3, rec4, rec5, rec6, rec7]):
                return

            # Если записи нет, создаем новую
            user = RecommendationSettings(
                user_id=user_id,
                rec1=rec1,
                rec2=rec2,
                rec3=rec3,
                rec4=rec4,
                rec5=rec5,
                rec6=rec6,
                rec7=rec7
            )
            session.add(user)
            await session.commit()



async def reset_recommendations(user_id: int, async_session: sessionmaker):
    async with async_session() as session:
        result = await session.execute(select(RecommendationSettings).filter_by(user_id=user_id))
        recommendation_settings = result.scalars().first()

        if recommendation_settings:
            recommendation_settings.rec1 = ""
            recommendation_settings.rec2 = ""
            recommendation_settings.rec3 = ""
            recommendation_settings.rec4 = ""
            recommendation_settings.rec5 = ""
            recommendation_settings.rec6 = ""
            recommendation_settings.rec7 = ""

            await session.commit()



async def get_rec(user_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(RecommendationSettings).where(RecommendationSettings.user_id == user_id)
            )
            recommendation = result.scalars().first()

            # Если запись не найдена или все поля пусты, возвращаем None
            if not recommendation or all(
                not getattr(recommendation, f"rec{i}") for i in range(1, 8)
            ):
                return None

            # Формируем словарь с ответами пользователя
            answers = {
                "rec1": recommendation.rec1,
                "rec2": recommendation.rec2,
                "rec3": recommendation.rec3,
                "rec4": recommendation.rec4,
                "rec5": recommendation.rec5,
                "rec6": recommendation.rec6,
                "rec7": recommendation.rec7,
            }

    return answers


async def get_liked_movies(user_id: int) -> list:
    """Получает все лайкнутые фильмы пользователя."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserPreferences.rec_like).where(
                    UserPreferences.user_id == user_id
                )
            )
            return [row[0] for row in result.fetchall() if row[0]]  # Возвращаем список IMDb ID



async def get_disliked_movies(user_id: int) -> set:
    """Получает все фильмы, которые пользователь пропустил."""
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserPreferences.rec_dis).where(
                    UserPreferences.user_id == user_id
                )
            )
            return {row[0] for row in result.fetchall() if row[0]}  # Возвращаем множество IMDb ID


async def add_to_likes(user_id: int, movie_id: str):
    async with async_session() as session:
        async with session.begin():
            new_like = UserPreferences(user_id=user_id, rec_like=movie_id)
            session.add(new_like)
            await session.commit()


async def add_to_next(user_id: int, movie_id: str):
    async with async_session() as session:
        async with session.begin():
            new_dislike = UserPreferences(user_id=user_id, rec_dis=movie_id)
            session.add(new_dislike)
            await session.commit()

async def add_to_unrec(user_id: int, movie_id: str):
    async with async_session() as session:
        async with session.begin():
            new_unrec = UserPreferences(user_id=user_id, unrecommended=movie_id)
            session.add(new_unrec)
            await session.commit()

async def save_movie_rating(user_id, movie_id):
    async with async_session() as session:
        async with session.begin():
            new_movie = UserPreferences(user_id=user_id, watched = movie_id)
            session.add(new_movie)
            await session.commit()

async def get_watched(user_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserPreferences.watched).where(
                    UserPreferences.user_id == user_id
                )
            )
            return [row[0] for row in result.fetchall() if row[0]]  # Возвращаем множество IMDb ID

async def get_unrec(user_id: int) -> list:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserPreferences.unrecommended).where(
                    UserPreferences.user_id == user_id
                )
            )
            return [row[0] for row in result.fetchall() if row[0]]  # Возвращаем список IMDb ID

async def remove_unrec(user_id: int, movie_id: str):
    async with async_session() as session:
        async with session.begin():
            # Удаляем запись с указанным user_id и movie_id
            await session.execute(
                delete(UserPreferences)
                .where(UserPreferences.user_id == user_id)
                .where(UserPreferences.unrecommended == movie_id)
            )
            await session.commit()  # Подтверждаем изменения






