from config import SQLALCHEMY_URL
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column
from sqlalchemy import BigInteger, DATETIME, Integer, Text, String
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker
from sqlalchemy import ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import BOOLEAN


# Создаем асинхронный движок и сессию
engine = create_async_engine(SQLALCHEMY_URL, echo=True, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для всех моделей
class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, unique=True, nullable=False)
    user_start_date = mapped_column(DATETIME, nullable=False)
    user_end_date = mapped_column(DATETIME)
    user_active = mapped_column(Boolean, default=True)  # Используем Boolean
    user_request_total: Mapped[int] = mapped_column()
    user_request: Mapped[int] = mapped_column()

    # Связь с подписками
    subscriptions = relationship("Subscriptions", back_populates="user")
    # Связь с рекомендациями
    recommendation_settings = relationship("RecommendationSettings", back_populates="user")
    # Связь с предпочтениями
    preferences = relationship("UserPreferences", back_populates="user")
    # Связь с лимитами
    limits = relationship("UserLimits", back_populates="user")


class Subscriptions(Base):
    __tablename__ = 'subscriptions'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    sub = mapped_column(Boolean, nullable=False)  # Подписка (True/False)
    sub_start = mapped_column(DATETIME, nullable=False)
    sub_end = mapped_column(DATETIME, nullable=False)
    sub_renewal = mapped_column(Boolean, default=False)  # Подписка продлевается (True/False)

    # Связь с пользователем
    user = relationship("User", back_populates="subscriptions")


class RecommendationSettings(Base):
    __tablename__ = 'recommendation_settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    rec_status: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rec1: Mapped[str] = mapped_column(String(250))
    rec2: Mapped[str] = mapped_column(String(250))
    rec3: Mapped[str] = mapped_column(String(250))
    rec4: Mapped[str] = mapped_column(String(250))
    rec5: Mapped[str] = mapped_column(String(250))
    rec6: Mapped[str] = mapped_column(String(250))
    rec7: Mapped[str] = mapped_column(String(250))

    # Связь с пользователем
    user = relationship("User", back_populates="recommendation_settings")


class UserPreferences(Base):
    __tablename__ = 'user_preferences'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    rec_like = mapped_column(Text)
    rec_dis = mapped_column(Text)
    watched = mapped_column(Text)
    unrecommended = mapped_column(Text)

    # Связь с пользователем
    user = relationship("User", back_populates="preferences")


class UserLimits(Base):
    __tablename__ = 'user_limits'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    limit: Mapped[int] = mapped_column()

    # Связь с пользователем
    user = relationship("User", back_populates="limits")


async def on_startup():
    # Создание всех таблиц в базе данных
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)