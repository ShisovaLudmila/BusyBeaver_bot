from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import types
import re
from create_bot import bot
from aiogram.filters import Command
from state_list import STATE_LIST_EMPLOYEE

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
    # Removed the check for existing profile to allow multiple profiles
    # Start the form filling process directly
    logger.info(f"User {message.from_user.id} is starting to fill a new employee profile.")
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
        "Выберите ваш часовой пояс (UTC) с помощью стрелок < > и нажмите на число для подтверждения:",
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
    logger.info(f"User {call.from_user.id} confirmed their time zone selection")
    data = await state.get_data()
    timezone_value = data.get("time_zone", 0)
    
    # Explicitly save the time zone value to state
    await state.update_data(time_zone=timezone_value)
    
    logger.info(f"User {call.from_user.id} selected time zone: UTC{'+' if timezone_value > 0 else ''}{timezone_value}")
    await state.set_state(employee.job_title)
    await call.message.answer(
        "Выберите должность из предложенных вариантов:", reply_markup=job_title_kb
    )


@router.callback_query(F.data == "фулл-тайм", employee.job_title)
async def job_title_selection_full_time(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected job title: {call.data}")
    await state.update_data(job_title=call.data)

    await state.set_state(employee.role)
    data = await state.get_data()
    role_kb = data.get("role", [])
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
    role_kb = data.get("role", [])
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
        "Отправьте ссылку на ваше резюме (Google Drive или Яндекс Диск):",
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
        domain_match = re.search(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
            message.text,
        )
        if domain_match and (
            domain_match[0] == "drive.google.com" or domain_match[0] == "disk.yandex.ru"
        ):
            await state.update_data(resume=message.text)
            logger.info(
                f"User {message.from_user.id} entered a valid resume link: {message.text}"
            )
            await message.answer(
                "Отправьте ссылку на вашу видео-визитку (Google Drive или Яндекс Диск):",
                reply_markup=questions_kb,
            )
            await state.set_state(employee.video)
        else:
            logger.warning(
                f"User {message.from_user.id} entered an invalid resume link domain: {domain_match[0] if domain_match else 'None'}"
            )
            await message.answer(
                "Пожалуйста, отправьте ссылку на Google Drive или Яндекс Диск:"
            )
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid resume link: {message.text}"
        )
        await message.answer(
            "Пожалуйста, отправьте корректную ссылку на Google Drive или Яндекс Диск:"
        )


@router.message(employee.video)
async def video(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} is entering their video link: {message.text}"
    )
    if re.fullmatch(r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$", message.text):
        domain_match = re.search(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
            message.text,
        )
        if domain_match and (
            domain_match[0] == "drive.google.com" or domain_match[0] == "disk.yandex.ru"
        ):
            await state.update_data(video=message.text)
            logger.info(
                f"User {message.from_user.id} entered a valid video link: {message.text}"
            )
            await update_on_reject(message, state)
        else:
            logger.warning(
                f"User {message.from_user.id} entered an invalid video link domain: {domain_match[0] if domain_match else 'None'}"
            )
            await message.answer(
                "Пожалуйста, отправьте ссылку на Google Drive или Яндекс Диск:"
            )
    else:
        logger.warning(
            f"User {message.from_user.id} entered an invalid video link: {message.text}"
        )
        await message.answer(
            "Пожалуйста, отправьте корректную ссылку на Google Drive или Яндекс Диск:"
        )


@router.message(F.text == "подтвердить", employee.confirm)
async def confirm_handler(message: types.Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} is confirming their data.")
    await state.update_data(tg_id=message.from_user.id)
    data = await state.get_data()
    
    # Ensure time_zone is an integer
    time_zone = data.get("time_zone", 0)
    if not isinstance(time_zone, int):
        try:
            time_zone = int(time_zone)
        except (ValueError, TypeError):
            time_zone = 0
    
    # Insert data into database
    db.insert_employee(
        data["tg_id"],
        data["name"],
        data["surname"],
        data["birthdate"],
        data["city"],
        time_zone,  # Use the integer time zone value
        data["job_title"],
        data.get("hours", ""),  # Use get with default for optional fields
        data["role"],
        year_of_exp_dict.get(data["year_of_exp"]),
        data["resume"],
        data["video"],
    )
    
    logger.info(
        f"User {message.from_user.id} data has been saved to the database with time_zone: {time_zone}"
    )
    
    # Send success message
    await message.answer(
        "Ваш аккаунт создан, теперь найти работу будет быстрее. Вы можете искать подходящие для вас вакансии и метчиться с работодателями!",
        reply_markup=main_kb
    )
    
    await state.clear()


async def update_on_reject(message: Message, state: FSMContext):
    await state.set_state(employee.confirm)
    data = await state.get_data()
    hours_info = data.get("hours", "")
    roles = ", ".join(data["role"]) if isinstance(data.get("role"), list) else data.get("role", "")
    
    # Format time zone with UTC prefix
    time_zone = data.get("time_zone", 0)
    time_zone_display = f"UTC{'+' if int(time_zone) > 0 else ''}{time_zone}"
    
    await state.update_data(hours=hours_info)
    await state.update_data(role=roles)
    hours_msg = f"<b>Количество часов</b>: {hours_info}\n" if hours_info != "" else ""
    
    logger.info(
        f"User {message.from_user.id} is reviewing their data before confirmation."
    )
    await message.answer(
        (
            f"Ваши данные указанные выше:\n"
            f"<b>Имя</b>: {data['name']}\n"
            f"<b>Фамилия</b>: {data['surname']}\n"
            f"<b>Дата рождения</b>: {data['birthdate']}\n"
            f"<b>Город</b>: {data['city']}\n"
            f"<b>Часовой пояс</b>: {time_zone_display}\n"
            f"<b>Должность</b>: {data['job_title']}\n"
            f"{hours_msg}"
            f"<b>Роли</b>: {roles}\n"
            f"<b>Кол-во лет опыта</b>: {data['year_of_exp']}\n"
            f"<b>Резюме</b>: {data['resume']}\n"
            f"<b>Видеовизитка</b>: {data['video']}\n"
        ),
        parse_mode="HTML",
        reply_markup=confirm_kb,
    )

@router.message(Command("на главное меню"), employee)
async def interrupt_with_main_menu(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} interrupted profile creation with main menu command")
    await state.clear()
    await message.answer("Создание профиля отменено. Вы вернулись в главное меню.", reply_markup=main_kb)

@router.message(Command("отмена"), employee)
async def interrupt_with_cancel(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} interrupted profile creation with cancel command")
    await state.clear()
    await message.answer("Создание профиля отменено.", reply_markup=main_kb)

@router.message(Command("помощь"), employee)
async def help_during_profile(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested help during profile creation")
    current_state = await state.get_state()
    
    await message.answer(
        "Вы находитесь в процессе создания профиля соискателя. "
        "Пожалуйста, следуйте инструкциям бота для заполнения всех полей. "
        "Вы можете использовать команду /отмена, чтобы прервать создание профиля, "
        "или /на_главное_меню, чтобы вернуться в главное меню.",
        reply_markup=None
    )
    
    # Continue with the current state
    state_item = next((item for item in STATE_LIST_EMPLOYEE if item.state_name == current_state), None)
    if state_item:
        await message.answer(state_item.state_question, reply_markup=state_item.keyboard)