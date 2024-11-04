from aiogram.fsm.state import State, StatesGroup
from dataclasses import dataclass
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove
from typing import Union
from all_kb import (
    create_role_kb,
    change_keyboard_time_zone,
    hours_kb,
    job_title_kb,
    year_of_exp_kb,
    first_question_kb,
    questions_kb,
    confirm_kb,
)
from typing import Callable


class employer(StatesGroup):
    company = State()
    city = State()
    time_zone = State()
    job_title = State()
    hours = State()
    role = State()
    year_of_exp = State()
    vacancy_description = State()
    salary_description = State()
    details = State()
    confirm = State()


class employee(StatesGroup):
    name = State()
    surname = State()
    birthdate = State()
    city = State()
    time_zone = State()
    job_title = State()
    hours = State()
    role = State()
    year_of_exp = State()
    resume = State()
    video = State()
    confirm = State()
    # confirm_reject= State()


class find_employee(StatesGroup):
    get_employee = State()


class find_job(StatesGroup):
    get_job = State()


class profile(StatesGroup):
    get_profile = State()
    delete_profile = State()


# class profile_employee(StatesGroup):
#     get_profile = State()
#     change_profile = State()
#     delete_profile = State()


class edit_employee(StatesGroup):
    choose_field = State()
    update_value = State()


class edit_employer(StatesGroup):
    choose_field = State()
    update_value = State()


class payments_states(StatesGroup):
    select_subscribe = State()
    pre_confirm_query = State()
    confirm_query = State()


@dataclass
class State:
    state_name: str
    state_question: str
    state_in_memory_name: str
    state_corresponding_button: str
    keyboard: Union[
        ReplyKeyboardMarkup,
        InlineKeyboardMarkup,
        Callable[[list[str]], InlineKeyboardMarkup],
        None,
    ] = None


STATE_LIST_EMPLOYEE = [
    State("employee:name", "Введите имя", "name", "Имя", first_question_kb),
    State("employee:surname", "Введите фамилию", "surname", "Фамилия", questions_kb),
    State(
        "employee:birthdate",
        "Введите дату рождения в формате дд.мм.гггг",
        "birthdate",
        "Дата рождения",
        questions_kb,
    ),
    State("employee:city", "Введите город проживания", "city", "Город", questions_kb),
    State(
        "employee:time_zone",
        "Выберете ваш часовой пояс стрелками < > и нажмите на число",
        "time_zone",
        "Часовой пояс",
        change_keyboard_time_zone(0),
    ),
    State(
        "employee:job_title",
        "Выберете должность из предложенных вариантов",
        "job_title",
        "Должность",
        job_title_kb,
    ),
    State(
        "employee:hours",
        "Сколько часов в день вы готовы работать",
        "hours",
        "Количество часов",
        hours_kb,
    ),
    State(
        "employee:role", "Выберите желаемую роль", "role", "Роль", create_role_kb([])
    ),
    State(
        "employee:year_of_exp",
        "Сколько у вас лет опыта",
        "year_of_exp",
        "Лет опыта",
        year_of_exp_kb,
    ),
    State(
        "employee:resume",
        "Отправьте свое резюме ссылкой на гугл или яндекс диск ",
        "resume",
        "Резюме",
        questions_kb,
    ),
    State(
        "employee:video",
        "Отправьте свою видео визитку ссылкой на гугл или андекс диск",
        "video",
        "Видео",
        questions_kb,
    ),
    State("employee:confirm", "", "", "", confirm_kb),
]

STATE_LIST_EMPLOYER = [
    State(
        "employer:company",
        "Введите название компании",
        "company",
        "Компания",
        first_question_kb,
    ),
    State("employer:city", "Введите город:", "city", "Город", questions_kb),
    State(
        "employer:time_zone",
        "Выберете ваш часовой пояс стрелками < > и нажмите на число",
        "time_zone",
        "Часовой пояс",
        change_keyboard_time_zone(0),
    ),
    State(
        "employer:job_title",
        "На какую должность нужен сотрудник",
        "job_title",
        "Должность",
        job_title_kb,
    ),
    State(
        "employer:hours",
        "На сколько часов в день нужен сотрудник",
        "hours",
        "Количество часов",
        hours_kb,
    ),
    State(
        "employer:role", "Выберите желаемую роль", "role", "Роль", create_role_kb([])
    ),
    State(
        "employer:year_of_exp",
        "Сколько нужно лет опыта:",
        "year_of_exp",
        "Лет опыта",
        year_of_exp_kb,
    ),
    State(
        "employer:vacancy_description",
        "Описание вакансии (не более 500 символов)",
        "vacancy_description",
        "Описание",
        questions_kb,
    ),
    State(
        "employer:salary_description",
        "Описание зарплатной вилки",
        "salary_description",
        "Зарплата",
        questions_kb,
    ),
    State(
        "employer:details",
        "Ссылка где можно узнать подробнее о компании",
        "details",
        "Узнать подробнее",
        questions_kb,
    ),
    State("employer:confirm", "", "", "", confirm_kb),
]
