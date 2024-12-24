from db.models import User, Subscriptions, UserPreferences, RecommendationSettings, UserLimits, async_session
from sqlalchemy.future import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy import update, delete, select
from datetime import datetime

async def set_user(id, user_start_date = datetime.now()  , user_end_date=datetime.now(), user_active=True, user_request_total=0,
                   user_request=0):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.id == id))

        if not user:  # Если пользователя нет в базе
            new_user = User(
                user_id=id,
                user_start_date=user_start_date,
                user_end_date=user_end_date,
                user_active=user_active,
                user_request_total=user_request_total,
                user_request=user_request
            )
            session.add(new_user)  # Добавляем нового пользователя
            await session.commit()  # Сохраняем изменения


async def check_and_add_recommendations(rec1, rec2, rec3, rec4, rec5, rec6, rec7, user_id, async_session: sessionmaker):
    async with async_session() as session:
        # Проверяем, есть ли уже настройки рекомендаций для этого пользователя
        result = await session.execute(select(RecommendationSettings).filter_by(user_id=user_id))
        recommendation_settings = result.scalars().first()  # Получаем первый результат

        if recommendation_settings:
            # Если запись уже существует, обновляем только пустые поля
            if not recommendation_settings.rec1 and rec1:
                recommendation_settings.rec1 = rec1
            if not recommendation_settings.rec2 and rec2:
                recommendation_settings.rec2 = rec2
            if not recommendation_settings.rec3 and rec3:
                recommendation_settings.rec3 = rec3
            if not recommendation_settings.rec4 and rec4:
                recommendation_settings.rec4 = rec4
            if not recommendation_settings.rec5 and rec5:
                recommendation_settings.rec5 = rec5
            if not recommendation_settings.rec6 and rec6:
                recommendation_settings.rec6 = rec6
            if not recommendation_settings.rec7 and rec7:
                recommendation_settings.rec7 = rec7

            await session.commit()  # Сохраняем изменения в базе данных

        else:
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
            await session.commit()  # Сохраняем новую запись


async def get_rec(user_id: int):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(RecommendationSettings).where(RecommendationSettings.user_id == user_id)
            )
            recommendation = result.scalars().first()

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

async def is_like(user_id: int, movie_id: str) -> bool:

    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserPreferences).where(
                    UserPreferences.user_id == user_id,
                    UserPreferences.rec_like == movie_id
                )
            )
            # Проверяем, есть ли такая запись
            return result.scalars().first() is not None




async def is_next(user_id: int, movie_id: str) -> bool:
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(UserPreferences).where(
                    UserPreferences.user_id == user_id,
                    UserPreferences.rec_dis == movie_id
                )
            )
            # Проверяем, есть ли такая запись
            return result.scalars().first() is not None


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
