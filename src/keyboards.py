from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.callback_data import Menu_Callback



subscribe_button  = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подписаться на канал', url=f"https://t.me/{os.getenv('TEST_CHANNEL_ID')}")],
    [InlineKeyboardButton(text='Проверить подписку', callback_data='check')]
])

main_menu_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Мой Профиль')],
                                [KeyboardButton(text='Рекомендации'),],
                                [KeyboardButton(text='Избранное')]], resize_keyboard=True, one_time_keyboard=True) #,[KeyboardButton(text='Выбрать фильм вместе')]

check_subscription_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Проверить подписку')]])

set_profile_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Давай')],
                                                   [KeyboardButton(text = 'На главную')]], resize_keyboard=True, one_time_keyboard=True)


profile_menu_buttons = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Сбросить рекомендации')],
                                                    #[KeyboardButton(text = 'Подписка')],
                                                    [KeyboardButton(text = 'На главную')]], resize_keyboard=True, one_time_keyboard=True)





favourites_button = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text='⏮️', callback_data='move_begin'),
     InlineKeyboardButton(text='◀️', callback_data='move_back'),
     InlineKeyboardButton(text='▶️', callback_data='move_forward'),
     InlineKeyboardButton(text='⏩', callback_data='move_end')
     ],
    [InlineKeyboardButton(text='На главную', callback_data='На главную')]
])

prev_button = InlineKeyboardButton(text="◀️", callback_data="show_list_prev")
next_button = InlineKeyboardButton(text="▶️", callback_data="show_list_next")

rate_buttons = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text='1', callback_data='1'),
            InlineKeyboardButton(text='2', callback_data='2'),
            InlineKeyboardButton(text='3', callback_data='3'),
            InlineKeyboardButton(text='4', callback_data='4'),
            InlineKeyboardButton(text='5', callback_data='5')
        ]
    ]
)

go_back_button = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = 'Назад')]], resize_keyboard=True, one_time_keyboard=True)

def user_recommendation_button(index: int):
    keyboard = InlineKeyboardBuilder()
    btns = {
        '❤️': 'like',
        'Следующий⏩': 'next',
        'Смотрел': 'watched',
        'Стоп': 'Стоп'
    }
    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=Menu_Callback(menu_name=menu_name, index=index).pack()))
    return keyboard.adjust(2, 1, 1).as_markup()

