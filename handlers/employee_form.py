from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import types
import re
from create_bot import bot

from state_list import employee
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
from create_bot import db, logger

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
@router.message(F.text == "соискатель")
async def employee_selection(message: Message, state: FSMContext):
    logger.info(f"Received message from user {message.from_user.id}: {message.text}")
    if db.get_tg_id_employee(message.from_user.id) != None:
        logger.info(f"User {message.from_user.id} already has a filled questionnaire.")
        await message.answer(
            "У вас уже есть заполненная анкета, по желанию вы можете получить данные или отредактировать данные ",
            reply_markup=main_kb,
        )
    else:
        # await message.answer("Для того, чтобы продолжить пользоваться сервисом, заполните данную анкету, строго отвечайте на заданные вопросы")
        logger.info(
            f"User {message.from_user.id} does not have a filled questionnaire. Starting new questionnaire."
        )
        await state.set_state(employee.name)
        await message.answer("Введите имя:", reply_markup=first_question_kb)


@router.message(employee.confirm, F.text == "начать сначала")
async def start_over_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} chose to start over.")
    await state.clear()
    await state.set_state(employee.name)
    await message.answer("Введите имя:", reply_markup=first_question_kb)


@router.message(employee.name)
async def name_selection(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is entering their name: {message.text}")
    if re.fullmatch(r"^\S+$", message.text):
        await state.update_data(name=message.text)
        logger.info(f"User {message.from_user.id} entered a valid name: {message.text}")
        await state.set_state(employee.surname)
        await message.answer("Введите фамилию:", reply_markup=questions_kb)
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid name: {message.text}"
        )
        await message.answer("Введите имя повторно:")


@router.message(employee.surname)
async def surname_selection(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} is entering their surname: {message.text}"
    )

    if re.fullmatch(r"^\S+$", message.text):
        await state.update_data(surname=message.text)
        logger.info(
            f"User {message.from_user.id} entered a valid surname: {message.text}"
        )
        await state.set_state(employee.birthdate)
        await message.answer(
            "Введите дату рождения в формате дд.мм.гггг:", reply_markup=questions_kb
        )
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid surname: {message.text}"
        )
        await message.answer("Введите фамилию повторно:")


@router.message(employee.birthdate)
async def birthdate_selection(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} is entering their birthdate: {message.text}"
    )

    if re.fullmatch(
        r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$", message.text
    ):
        await state.update_data(birthdate=message.text)
        logger.info(
            f"User {message.from_user.id} entered a valid birthdate: {message.text}"
        )
        await state.set_state(employee.city)
        await message.answer("Введите город проживания:", reply_markup=questions_kb)
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid birthdate: {message.text}"
        )
        await message.answer("Введите дату рождения повторно в формате дд.мм.гггг:")


@router.message(employee.city)
async def city_selection(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is entering their city: {message.text}")
    await state.update_data(city=message.text)
    logger.info(f"User {message.from_user.id} entered their city: {message.text}")
    await state.set_state(employee.time_zone)

    await message.answer(
        "Выберете ваш часовой пояс стрелками < > и нажмите на число",
        reply_markup=change_keyboard_time_zone(),
    )


@router.callback_query(
    F.data.in_(["decrease", "increase"]),
    employee.time_zone,
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
    employee.time_zone,
)
async def callback_timezone_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} is entering their time zone: {call.data}")

    logger.info(f"User {call.from_user.id} entered a valid time zone: {call.data}")
    await state.set_state(employee.job_title)
    await call.message.answer(
        "Выберете должность из предложенных вариантов:", reply_markup=job_title_kb
    )


@router.callback_query(F.data == "фулл-тайм", employee.job_title)
async def job_title_selection_full_time(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)

    await state.set_state(employee.role)
    data = await state.get_data()
    role_kb = data["role"] if "role" in data else []
    logger.info(f"User {call.from_user.id} is selecting a role.")
    await call.message.answer(
        "Выберите желаемую роль:", reply_markup=create_role_kb(role_kb)
    )
    await call.answer()


@router.callback_query(F.data == "парт-тайм", employee.job_title)
async def job_title_selection_part_time(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)

    await state.set_state(employee.hours)
    logger.info(f"User {call.from_user.id} is selecting hours per day.")
    await call.message.answer(
        "Сколько часов в день вы готовы работать:", reply_markup=hours_kb
    )
    await call.answer()


@router.callback_query(F.data == "оба варианта", employee.job_title)
async def job_title_selection_both(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)

    await state.set_state(employee.hours)
    logger.info(f"User {call.from_user.id} is selecting hours per day.")
    await call.message.answer(
        "Сколько часов в день вы готовы работать:", reply_markup=hours_kb
    )
    await call.answer()


@router.callback_query(F.data.in_(["1", "2", "3", "4", "5", "6", "7"]), employee.hours)
async def hours_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected hours per day: {call.data}")
    await state.update_data(hours=call.data)

    data = await state.get_data()
    role_kb = data["role"] if "role" in data else []
    logger.info(f"User {call.from_user.id} is selecting a role.")
    await call.message.answer(
        "Выберите желаемую роль:", reply_markup=create_role_kb(role_kb)
    )
    await state.set_state(employee.role)
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
    employee.role,
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
            "Сколько у вас лет опыта:", reply_markup=year_of_exp_kb
        )
        await state.set_state(employee.year_of_exp)
        await call.answer()


@router.callback_query(
    F.data.in_(["0-1", "1-3", "3-5", "5-7", "7-10", "больше 10"]), employee.year_of_exp
)
async def year_of_exp_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected years of experience: {call.data}")
    await state.update_data(year_of_exp=call.data)

    logger.info(f"User {call.from_user.id} is asked to send their resume.")
    await call.message.answer(
        "Отправьте свое резюме ссылкой на гугл или андекс диск:",
        reply_markup=questions_kb,
    )
    await state.set_state(employee.resume)
    await call.answer()


@router.message(employee.resume)
async def resume(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} is entering their resume link: {message.text}"
    )
    if re.fullmatch(r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$", message.text):
        if (
            re.search(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
                message.text,
            )[0]
            == "drive.google.com"
            or re.search(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
                message.text,
            )[0]
            == "disk.yandex.ru"
        ):
            await state.update_data(resume=message.text)
            logger.info(
                f"User {message.from_user.id} entered a valid resume link: {message.text}"
            )
            await message.answer(
                "Отправьте свою видео визитку ссылкой на гугл или андекс диск:",
                reply_markup=questions_kb,
            )
            await state.set_state(employee.video)
        else:
            logger.warning(
                f"User {message.from_user.id} entered an invalid resume link domain: {re.search(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', message.text)[0]}"
            )
            await message.answer(
                "Отправьте свое резюме повторно ссылкой на гугл или андекс диск:"
            )
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid resume link: {message.text}"
        )
        await message.answer(
            "Отправьте свое резюме повторно ссылкой на гугл или яндекс диск:"
        )


@router.message(employee.video)
async def video(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} is entering their video link: {message.text}"
    )
    if re.fullmatch(r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$", message.text):
        if (
            re.search(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
                message.text,
            )[0]
            == "drive.google.com"
            or re.search(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
                message.text,
            )[0]
            == "disk.yandex.ru"
        ):
            await state.update_data(video=message.text)
            logger.info(
                f"User {message.from_user.id} entered a valid video link: {message.text}"
            )
            await update_on_reject(message, state)
        else:
            logger.warning(
                f"User {message.from_user.id} entered an invalid video link domain: {re.search(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]', message.text)[0]}"
            )
            await message.answer(
                "Отправьте свою видео визитку повторно ссылкой на гугл или андекс диск:"
            )
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid video link: {message.text}"
        )
        await message.answer(
            "Отправьте свою видео визитку повторно ссылкой на гугл или андекс диск:"
        )


@router.message(F.text == "подтвердить", employee.confirm)
async def confirm_handler(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is confirming their data.")
    await state.update_data(tg_id=message.from_user.id)
    data = await state.get_data()
    await message.answer("Спасибо за вашу форму!", reply_markup=main_kb)
    db.insert_employee(
        data["tg_id"],
        data["name"],
        data["surname"],
        data["birthdate"],
        data["city"],
        data["time_zone"],
        data["job_title"],
        data["hours"],
        data["role"],
        year_of_exp_dict.get(data["year_of_exp"]),
        data["resume"],
        data["video"],
    )
    logger.info(
        f"User {message.from_user.id} data has been saved to the database with the following values:\n"
        f"tg_id: {data['tg_id']}, name: {data['name']}, surname: {data['surname']}, birthdate: {data['birthdate']},\n"
        f"city: {data['city']}, time_zone: {data['time_zone']}, job_title: {data['job_title']}, hours: {data['hours']},\n"
        f"role: {data['role']}, year_of_exp: {year_of_exp_dict.get(data['year_of_exp'])}, resume: {data['resume']}, video: {data['video']}"
    )
    await state.clear()


async def update_on_reject(message: Message, state: FSMContext):
    await state.set_state(employee.confirm)
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
            f"<b>Имя</b>: {data['name']}\n"
            f"<b>Фамилия</b>: {data['surname']}\n"
            f"<b>Дата рождения</b>: {data['birthdate']}\n"
            f"<b>Город</b>: {data['city']}\n"
            f"<b>Часовой пояс</b>: {data['time_zone']}\n"
            f"<b>Должность</b>: {data['job_title']}\n"
            f"{hours_msg}"
            f"<b>Рол</b>:{data['role']}\n"
            f"<b>Кол-во лет опыта</b>: {data['year_of_exp']}\n"
            f"<b>Резюме</b>: {data['resume']}\n"
            f"<b>Видеовизитка</b>: {data['video']}\n"
        ),
        parse_mode="HTML",
        reply_markup=confirm_kb,
    )
