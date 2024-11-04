from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import types
import re
from datetime import datetime, timedelta
from state_list import employer
from create_bot import db, logger
from all_kb import (
    job_title_kb,
    create_role_kb,
    hours_kb,
    year_of_exp_kb,
    confirm_kb,
    first_question_kb,
    questions_kb,
    main_kb,
    change_keyboard_time_zone,
)


year_of_exp_dict = {
    "0-1": "0",
    "1-3": "1",
    "3-5": "3",
    "5-7": "5",
    "7-10": "7",
    "больше 10": "10",
}

router = Router()


# хендлер для кнопки соискатель
@router.message(F.text == "работодатель")
async def employer_selection(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} selected 'работодатель'.")
    if (
        message.date.replace(tzinfo=None)
        <= datetime.strptime("2024-09-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        and db.get_end_of_free_week_subscription is None
    ):
        await message.answer(
            "Как новый пользователь вы получаете, бесплатную пробную подписку на 1 неделю"
        )
        db.set_free_week_subscription(
            message.from_user.id, message.date.replace(tzinfo=None) + timedelta(hours=3)
        )
        logger.info(f"User {message.from_user.id} received a free week subscription.")
    else:
        logger.info(
            f"User {message.from_user.id} did not receive a free week subscription due to date constraints."
        )
    if db.get_tg_id_employer(message.from_user.id) != None:
        await message.answer(
            "У вас уже есть заполненная анкета, по желанию вы можете получить данные или отредактировать данные ",
            reply_markup=main_kb,
        )
        logger.info(f"User {message.from_user.id} already has a filled form.")
    else:
        # await message.answer("Для того, чтобы продолжить пользоваться сервисом, заполните данную анкету, строго отвечайте на заданные вопросы")
        await state.set_state(employer.company)
        await message.answer(
            "Введите название компании:", reply_markup=first_question_kb
        )
        logger.info(f"User {message.from_user.id} is starting to fill out the form.")


@router.message(employer.confirm, F.text == "начать сначала")
async def start_over_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} chose to start over.")
    await state.clear()
    await state.set_state(employer.company)
    await message.answer("Введите название компании:", reply_markup=first_question_kb)


@router.message(employer.company)
async def name_selection(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered company name: {message.text}")
    await state.update_data(company=message.text)
    await state.set_state(employer.city)
    await message.answer("Введите город:", reply_markup=questions_kb)


@router.message(employer.city)
async def city_selection(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered company city: {message.text}")
    await state.update_data(city=message.text)
    await state.set_state(employer.time_zone)
    await message.answer(
        "Выберете ваш часовой пояс стрелками < > и нажмите на число",
        reply_markup=change_keyboard_time_zone(),
    )


@router.callback_query(
    F.data.in_(["decrease", "increase"]),
    employer.time_zone,
)
async def callback_change_timezone(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    timezone_value = data.get("time_zone", 0)  # Получаем текущее значение из состояния

    if call.data == "increase" and timezone_value < 14:
        timezone_value += 1
    elif call.data == "decrease" and timezone_value > -12:
        timezone_value -= 1

    # Обновляем значение в состоянии
    await state.update_data(time_zone=timezone_value)

    # Создаем новую клавиатуру с обновленным значением
    keyboard = change_keyboard_time_zone(timezone_value)
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(
    F.data == "time_zone_callback",
    employer.time_zone,
)
async def callback_timezone_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} is entering their time zone: {call.data}")
    # data = await state.get_data()
    # reject = data.get("reject", False)
    # if reject:
    #     await update_on_reject(message, state)
    # else:
    logger.info(f"User {call.from_user.id} entered a valid time zone: {call.data}")
    await state.set_state(employer.job_title)
    await call.message.answer(
        "На какую должность нужен сотрудник:", reply_markup=job_title_kb
    )


@router.callback_query(F.data == "фулл-тайм", employer.job_title)
async def job_title_selection_full_time(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)
    await state.set_state(employer.role)
    data = await state.get_data()
    role_kb = data["role"] if "role" in data else []
    logger.info(f"User {call.from_user.id} is selecting a role.")
    await call.message.answer(
        "Выберите желаемую роль:", reply_markup=create_role_kb(role_kb)
    )
    await call.answer()


@router.callback_query(F.data == "парт-тайм", employer.job_title)
async def job_title_selection_part_time(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)
    await state.set_state(employer.hours)
    logger.info(f"User {call.from_user.id} is selecting hours per day.")
    await call.message.answer(
        "На сколько часов в день нужен сотрудник:", reply_markup=hours_kb
    )
    await call.answer()


@router.callback_query(F.data == "оба варианта", employer.job_title)
async def job_title_selection_both(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)
    await state.set_state(employer.hours)
    logger.info(f"User {call.from_user.id} is selecting hours per day.")
    await call.message.answer(
        "На сколько часов в день нужен сотрудник:", reply_markup=hours_kb
    )
    await call.answer()


@router.callback_query(F.data.in_(["1", "2", "3", "4", "5", "6", "7"]), employer.hours)
async def hours_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected hours per day: {call.data}")
    await state.update_data(hours=call.data)
    data = await state.get_data()
    role_kb = data["role"] if "role" in data else []
    logger.info(f"User {call.from_user.id} is selecting a role.")
    await call.message.answer(
        "Выберите желаемую роль:", reply_markup=create_role_kb(role_kb)
    )
    await state.set_state(employer.role)
    await call.answer()


@router.callback_query(
    F.data.in_(
        [
            "менеджер",
            "личный ассистент",
            "менеджер по закупкам",
            "дизайнер",
            "смм менеджер",
            "role_done",
        ]
    ),
    employer.role,
)
async def role_selection(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    role_data = data.get("role", [])

    if call.data != "role_done":
        if call.data in role_data:
            role_data.remove(call.data)
        else:
            role_data.append(call.data)

        await state.update_data(role=role_data)
        new_kb = create_role_kb(role_data)

        old_kb = call.message.reply_markup.inline_keyboard
        new_kb_list = new_kb.inline_keyboard
        if old_kb != new_kb_list:
            await call.message.edit_reply_markup(reply_markup=new_kb)
    else:
        logger.info(f"User {call.from_user.id} completed role selection.")
        await call.message.answer(
            "Сколько нужно лет опыта:", reply_markup=year_of_exp_kb
        )
        await state.set_state(employer.year_of_exp)
        await call.answer()


@router.callback_query(
    F.data.in_(["0-1", "1-3", "3-5", "5-7", "7-10", "больше 10"]),
    employer.year_of_exp,
)
async def year_of_exp_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected years of experience: {call.data}")
    await state.update_data(year_of_exp=call.data)
    logger.info(f"User {call.from_user.id} is asked to send their resume.")
    await call.message.answer("Описание вакансии :", reply_markup=questions_kb)
    await state.set_state(employer.vacancy_description)
    await call.answer()


@router.message(employer.vacancy_description)
async def description(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered vacancy description: {message.text}"
    )
    await state.update_data(vacancy_description=message.text)
    await message.answer("Описание зарплатной вилки:", reply_markup=questions_kb)
    await state.set_state(employer.salary_description)


@router.message(employer.salary_description)
async def salary(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered salary description: {message.text}"
    )
    await state.update_data(salary_description=message.text)
    await message.answer(
        "Ссылка где можно узнать подробнее о компании:", reply_markup=questions_kb
    )
    await state.set_state(employer.details)


@router.message(employer.details)
async def about_company(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered company details link: {message.text}"
    )
    if re.fullmatch(r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$", message.text):
        await state.update_data(details=message.text)
        logger.info(
            f"User {message.from_user.id} entered a valid company details link: {message.text}"
        )
        await update_on_reject(message, state)
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid company details link: {message.text}"
        )
        await message.answer(
            "Отправьте повтроно сслыку где узнать подробнее о компании:",
        )


@router.message(F.text == "подтвердить", employer.confirm)
async def confirm_handler(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is confirming their data.")
    await state.update_data(tg_id=message.from_user.id)
    data = await state.get_data()
    await message.answer("Спасибо за вашу форму!", reply_markup=main_kb)
    db.insert_employer(
        data["tg_id"],
        data["company"],
        data["city"],
        data["time_zone"],
        data["job_title"],
        data["hours"],
        data["role"],
        year_of_exp_dict.get(data["year_of_exp"]),
        data["vacancy_description"],
        data["salary_description"],
        data["details"],
    )
    logger.info(
        f"User {message.from_user.id} data has been saved to the database with the following values:\n"
        f"tg_id: {data['tg_id']}, company: {data['company']}, city: {data['city']}, time_zone: {data['time_zone']},\n"
        f"job_title: {data['job_title']}, hours: {data['hours']}, role: {data['role']},\n"
        f"year_of_exp: {year_of_exp_dict.get(data['year_of_exp'])}, vacancy_description: {data['vacancy_description']},\n"
        f"salary_description: {data['salary_description']}, details: {data['details']}"
    )
    await state.clear()


async def update_on_reject(message: Message, state: FSMContext):
    await state.set_state(employer.confirm)
    data = await state.get_data()
    hours_info = data["hours"] if "hours" in data else ""
    roles = ", ".join(data["role"]) if "role" in data else ""
    await state.update_data(hours=hours_info)
    await state.update_data(role=roles)
    hours_msg = f"<b>Количество часов</b>: {hours_info}\n" if hours_info != "" else ""
    data = await state.get_data()
    logger.info(
        f"User {message.from_user.id} is reviewing their data before confirmation."
    )
    await message.answer(
        (
            f"Ваш данные указанные выше:\n"
            f"<b>Компания</b>: {data['company']}\n"
            f"<b>Город</b>: {data['city']}\n"
            f"<b>Часовой пояс</b>: {data['time_zone']}\n"
            f"<b>Должность</b>: {data['job_title']}\n"
            f"{hours_msg}"
            f"<b>Роли</b>: {data['role']}\n"
            f"<b>Кол-во лет опыта</b>: {data['year_of_exp']}\n"
            f"<b>Описание вакансии</b>: {data['vacancy_description']}\n"
            f"<b>Зарплатная ветка</b>: {data['salary_description']}\n"
            f"<b>Узнать подробнее</b>: {data['details']}\n"
        ),
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_markup=confirm_kb,
    )
