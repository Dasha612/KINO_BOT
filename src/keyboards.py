from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
import os
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.callback_data import Menu_Callback



subscribe_button  = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Подписаться на канал', url=f"https://t.me/{os.getenv('TEST_CHANNEL_ID')}")],
    [InlineKeyboardButton(text='Проверить подписку', callback_data='check')]
])


favourites_button = InlineKeyboardMarkup(inline_keyboard=[
     [InlineKeyboardButton(text='⏮️', callback_data='move_begin'),
     InlineKeyboardButton(text='◀️', callback_data='move_back'),
     InlineKeyboardButton(text='▶️', callback_data='move_forward'),
     InlineKeyboardButton(text='⏩', callback_data='move_end')
     ],
    [InlineKeyboardButton(text='На главную', callback_data='main')]
])

prev_button = InlineKeyboardButton(text="◀️", callback_data="show_list_prev")
next_button = InlineKeyboardButton(text="▶️", callback_data="show_list_next")
button_main = InlineKeyboardButton(text="На главную", callback_data="main")

# Создаём клавиатуру и добавляем кнопку
main = InlineKeyboardMarkup(inline_keyboard=[[button_main]])

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

# Главное меню (Main Menu)
main_menu_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Мой Профиль', callback_data='my_profile')],
    [InlineKeyboardButton(text='Рекомендации', callback_data='recommendations')],
    [InlineKeyboardButton(text='Избранное', callback_data='favourites')],
    # [InlineKeyboardButton(text='Выбрать фильм вместе', callback_data='main_choose_movie')]
])

# Кнопки для установки профиля (Set Profile)
set_profile_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Давай', callback_data='set_profile')],
    [InlineKeyboardButton(text='На главную', callback_data='main')]
])

# Кнопки меню профиля (Profile Menu)
profile_menu_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Сбросить рекомендации', callback_data='profile_reset_recommendations')],
    # [InlineKeyboardButton(text='Подписка', callback_data='profile_subscription')],
    [InlineKeyboardButton(text='На главную', callback_data='main')]
])
