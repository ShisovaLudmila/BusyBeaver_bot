from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram import types

start_buttons = [
    [KeyboardButton(text="соискатель"), KeyboardButton(text="работодатель")],
    [KeyboardButton(text="на главное меню")],
]
choose_role_kb = ReplyKeyboardMarkup(
    keyboard=start_buttons,
    resize_keyboard=True,
)

def get_main_kb(is_employer=False):
    """Return the main keyboard based on user type"""
    buttons = [
        [KeyboardButton(text="поиск работы"), KeyboardButton(text="поиск сотрудников")],
        [
            KeyboardButton(text="заполнить профиль"),
            KeyboardButton(text="редактировать профиль"),
            KeyboardButton(text="удалить профиль"),
        ],
        [KeyboardButton(text="помощь и обратная связь")]
    ]
    
    # Add subscription button only for employers
    if is_employer:
        buttons.append([KeyboardButton(text="подписка для работодателей")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# Default main keyboard (without subscription button)
main_buttons = [
    [KeyboardButton(text="поиск работы"), KeyboardButton(text="поиск сотрудников")],
    [
        # KeyboardButton(text="профиль"),
        KeyboardButton(text="заполнить профиль"),
        KeyboardButton(text="редактировать профиль"),
        KeyboardButton(text="удалить профиль"),
    ],
    [
        KeyboardButton(text="помощь и обратная связь"),
        #KeyboardButton(text="подписка для работодателей"),
    ],
]
main_kb = ReplyKeyboardMarkup(keyboard=main_buttons, resize_keyboard=True)

# Employer main keyboard (with subscription button)
employer_main_buttons = [
    [KeyboardButton(text="поиск работы"), KeyboardButton(text="поиск сотрудников")],
    [
        KeyboardButton(text="заполнить профиль"),
        KeyboardButton(text="редактировать профиль"),
        KeyboardButton(text="удалить профиль"),
    ],
    [
        KeyboardButton(text="помощь и обратная связь"),
        KeyboardButton(text="подписка для работодателей"),
    ],
]
employer_main_kb = ReplyKeyboardMarkup(keyboard=employer_main_buttons, resize_keyboard=True)

job_title_buttons = [
    [
        InlineKeyboardButton(text="фулл-тайм", callback_data="фулл-тайм"),
        InlineKeyboardButton(text="парт-тайм", callback_data="парт-тайм"),
    ],
    [InlineKeyboardButton(text="оба варианта", callback_data="оба варианта")],
]
job_title_kb = InlineKeyboardMarkup(inline_keyboard=job_title_buttons)


def change_keyboard_time_zone(timezone_value=0):
    timezone_display = f"UTC{'+' if timezone_value > 0 else ''}{timezone_value}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="<", callback_data="decrease"),
                InlineKeyboardButton(text=timezone_display, callback_data="time_zone_callback"),
                InlineKeyboardButton(text=">", callback_data="increase"),
            ]
        ]
    )
    return keyboard


hours_buttons = [
    [
        InlineKeyboardButton(text="1", callback_data="1"),
        InlineKeyboardButton(text="2", callback_data="2"),
        InlineKeyboardButton(text="3", callback_data="3"),
        InlineKeyboardButton(text="4", callback_data="4"),
        InlineKeyboardButton(text="5", callback_data="5"),
        InlineKeyboardButton(text="6", callback_data="6"),
        InlineKeyboardButton(text="7", callback_data="7"),
    ]
]
hours_kb = InlineKeyboardMarkup(inline_keyboard=hours_buttons)


def create_role_kb(selected_roles):
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(
            text=f"менеджер {'✅' if 'менеджер' in selected_roles else ''}",
            callback_data="менеджер",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"личный ассистент {'✅' if 'личный ассистент' in selected_roles else ''}",
            callback_data="личный ассистент",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"менеджер по закупкам {'✅' if 'менеджер по закупкам' in selected_roles else ''}",
            callback_data="менеджер по закупкам",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"дизайнер {'✅' if 'дизайнер' in selected_roles else ''}",
            callback_data="дизайнер",
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"смм менеджер {'✅' if 'смм менеджер' in selected_roles else ''}",
            callback_data="смм менеджер",
        )
    )
    builder.row(InlineKeyboardButton(text="продолжить", callback_data="role_done"))
    return builder.as_markup()


year_of_exp_buttons = [
    [
        InlineKeyboardButton(text="0-1", callback_data="0-1"),
        InlineKeyboardButton(text="1-3", callback_data="1-3"),
        InlineKeyboardButton(text="3-5", callback_data="3-5"),
        InlineKeyboardButton(text="5-7", callback_data="5-7"),
        InlineKeyboardButton(text="7-10", callback_data="7-10"),
    ],
    [InlineKeyboardButton(text="больше 10", callback_data="больше 10")],
]
year_of_exp_kb = InlineKeyboardMarkup(inline_keyboard=year_of_exp_buttons)

first_question_buttons = [
    [KeyboardButton(text="отмена")],
]
first_question_kb = ReplyKeyboardMarkup(
    keyboard=first_question_buttons, resize_keyboard=True
)

questions_buttons = [[KeyboardButton(text="назад"), KeyboardButton(text="отмена")]]
questions_kb = ReplyKeyboardMarkup(keyboard=questions_buttons, resize_keyboard=True)


confirm_buttons = [
    [KeyboardButton(text="назад"), KeyboardButton(text="отмена")],
    [KeyboardButton(text="подтвердить"), KeyboardButton(text="начать сначала")],
]

confirm_kb = ReplyKeyboardMarkup(keyboard=confirm_buttons, resize_keyboard=True)

change_employee_buttons_1 = [
    [],
    [
        KeyboardButton(text="Имя"),
        KeyboardButton(text="Фамилия"),
        KeyboardButton(text="Дата рождения"),
    ],
    [
        KeyboardButton(text="Город"),
        KeyboardButton(text="Часовой пояс"),
        KeyboardButton(text="Должность"),
    ],
    [
        KeyboardButton(text="Количество часов"),
        KeyboardButton(text="Роль"),
        KeyboardButton(text="Лет опыта"),
    ],
    [
        KeyboardButton(text="Резюме"),
        KeyboardButton(text="Видео"),
        KeyboardButton(text="на главное меню"),
    ],
]
change_employee_kb_1 = ReplyKeyboardMarkup(
    keyboard=change_employee_buttons_1, resize_keyboard=True
)
change_employee_buttons_2 = [
    [],
    [
        KeyboardButton(text="Имя"),
        KeyboardButton(text="Фамилия"),
        KeyboardButton(text="Дата рождения"),
    ],
    [
        KeyboardButton(text="Город"),
        KeyboardButton(text="Часовой пояс"),
        KeyboardButton(text="Должность"),
    ],
    [
        KeyboardButton(text="Роль"),
        KeyboardButton(text="Лет опыта"),
        KeyboardButton(text="Резюме"),
    ],
    [KeyboardButton(text="Видео"), KeyboardButton(text="на главное меню")],
]
change_employee_kb_2 = ReplyKeyboardMarkup(
    keyboard=change_employee_buttons_2, resize_keyboard=True
)

change_employer_buttons_1 = [
    [],
    [
        KeyboardButton(text="Компания"),
        KeyboardButton(text="Город"),
        KeyboardButton(text="Часовой пояс"),
    ],
    [
        KeyboardButton(text="Должность"),
        KeyboardButton(text="Количество часов"),
        KeyboardButton(text="Роль"),
    ],
    [
        KeyboardButton(text="Лет опыта"),
        KeyboardButton(text="Описании вакансии"),
        KeyboardButton(text="Зарплатная ветка"),
    ],
    [KeyboardButton(text="Узнать подробнее"), KeyboardButton(text="на главное меню")],
]
change_employer_kb_1 = ReplyKeyboardMarkup(
    keyboard=change_employer_buttons_1, resize_keyboard=True
)
change_employer_buttons_2 = [
    [],
    [
        KeyboardButton(text="Компания"),
        KeyboardButton(text="Город"),
        KeyboardButton(text="Часовой пояс"),
    ],
    [
        KeyboardButton(text="Должность"),
        KeyboardButton(text="Роль"),
        KeyboardButton(text="Лет опыта"),
    ],
    [
        KeyboardButton(text="Описании вакансии"),
        KeyboardButton(text="Зарплатная ветка"),
        KeyboardButton(text="Узнать подробнее"),
    ],
    [KeyboardButton(text="на главное меню")],
]
change_employer_kb_2 = ReplyKeyboardMarkup(
    keyboard=change_employer_buttons_2, resize_keyboard=True
)


get_data_buttons = [
    [KeyboardButton(text="для соискателя"), KeyboardButton(text="для работодателя")],
    [KeyboardButton(text="на главное меню")],
]

in_profile_buttons = [
    [KeyboardButton(text="изменить анкету"), KeyboardButton(text="на главное меню")],
]

in_profile_kb = ReplyKeyboardMarkup(keyboard=in_profile_buttons, resize_keyboard=True)


get_data_kb = ReplyKeyboardMarkup(keyboard=get_data_buttons, resize_keyboard=True)

get_employer_buttons = [
    [KeyboardButton(text="далее"), KeyboardButton(text="на главное меню")]
]
get_employer_kb = ReplyKeyboardMarkup(
    keyboard=get_employer_buttons, resize_keyboard=True
)


class MyCallback(CallbackData, prefix="rsd"):
    path: str
    user_tg_id: int


class MyCallback_after(CallbackData, prefix="after_rsd"):
    path: str
    employer_tg_id: int
    employee_tg_id: int
    username: str
    state: str


after_respond_buttons_1 = [
    [InlineKeyboardButton(text="вы откликнулись ✅", callback_data=" ")]
]
after_respond_kb_1 = InlineKeyboardMarkup(inline_keyboard=after_respond_buttons_1)

kb_after_respond_buttons_2 = [
    [InlineKeyboardButton(text="наняли ✅", callback_data=" ")]
]
after_respond_kb_2 = InlineKeyboardMarkup(inline_keyboard=kb_after_respond_buttons_2)

contact_buttons = [[InlineKeyboardButton(text="связались ✅", callback_data=" ")]]
contact_kb = InlineKeyboardMarkup(inline_keyboard=contact_buttons)

reject_buttons = [[InlineKeyboardButton(text="отклонили ✅", callback_data=" ")]]
reject_kb = InlineKeyboardMarkup(inline_keyboard=reject_buttons)


class Payments_callback(CallbackData, prefix="pay"):
    path: str
    label: str
    amount: int
