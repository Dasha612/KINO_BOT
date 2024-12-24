from aiogram import Bot, Dispatcher, types
import logging
import asyncio
import os
from aiogram.fsm.storage.memory import MemoryStorage


from config import bot
from dotenv import load_dotenv
from handlers import router
from db.models import on_startup


dp = Dispatcher(storage=MemoryStorage())
async def main():
    await on_startup()

    dp.include_router(router)
    await dp.start_polling(bot)


# Запуск бота
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Off")
