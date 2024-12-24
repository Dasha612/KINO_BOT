from sys import prefix

from aiogram.filters.callback_data import CallbackData
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder



subscribe_button  = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подписаться на канал', url=f"https://t.me/{os.getenv('TEST_CHANNEL_ID')}")],
    [InlineKeyboardButton(text='Проверить подписку', callback_data='check')]
])

main_menu_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Мой Профиль')],
                                [KeyboardButton(text='Рекомендации'),],
                                [KeyboardButton(text='Избранное')],
                                [KeyboardButton(text='Выбрать фильм вместе')]], resize_keyboard=True)

check_subscription_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Проверить подписку')]])

set_profile_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Давай')],
                                                   [KeyboardButton(text = 'На главную')]], resize_keyboard=True, one_time_keyboard=True)





class Menu_Callback(CallbackData, prefix='menu'):
    menu_name : str
    index: int

rate_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='1', callback_data='1')],
    [InlineKeyboardButton(text='2', callback_data='2')],
    [InlineKeyboardButton(text='2', callback_data='3')],
    [InlineKeyboardButton(text='2', callback_data='4')],
    [InlineKeyboardButton(text='2', callback_data='5')],
])

go_back_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Назад')]], resize_keyboard=True, one_time_keyboard=True)

def user_recommendation_button(index: int):
    keyboard = InlineKeyboardBuilder()
    btns = {
        '❤️': 'like',
        'Следующий⏩': 'next',
        'Смотрел': 'watched'
    }
    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=Menu_Callback(menu_name=menu_name, index=index).pack()))
    return keyboard.adjust(2, 1, 1).as_markup()

