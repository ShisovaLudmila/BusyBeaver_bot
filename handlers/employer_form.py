from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import types
import re
from datetime import datetime, timedelta
from state_list import employer
from create_bot import db, logger
from aiogram.filters import Command
from state_list import STATE_LIST_EMPLOYER
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


# хендлер для кнопки работодатель
@router.message(F.text == "работодатель")
async def employer_selection(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} selected 'работодатель'.")
    
    # Check for free trial eligibility
    if (
        message.date.replace(tzinfo=None)
        <= datetime.strptime("2024-09-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        and db.get_end_of_free_week_subscription(message.from_user.id) is None
    ):
        await message.answer(
            "Как новый пользователь вы получаете бесплатную пробную подписку на 1 неделю"
        )
        db.set_free_week_subscription(
            message.from_user.id, message.date.replace(tzinfo=None) + timedelta(hours=3)
        )
        logger.info(f"User {message.from_user.id} received a free week subscription.")
    else:
        logger.info(
            f"User {message.from_user.id} did not receive a free week subscription due to date constraints."
        )
    
    # Removed the check for existing profile to allow multiple profiles
    # Start the form filling process directly
    logger.info(f"User {message.from_user.id} is starting to fill a new employer profile.")
    await state.set_state(employer.company)
    await message.answer(
        "Введите название компании:", reply_markup=first_question_kb
    )


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
        "Выберите ваш часовой пояс (UTC) с помощью стрелок < > и нажмите на число для подтверждения:",
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
    logger.info(f"User {call.from_user.id} confirmed their time zone selection")
    data = await state.get_data()
    timezone_value = data.get("time_zone", 0)
    
    # Explicitly save the time zone value to state
    await state.update_data(time_zone=timezone_value)
    
    logger.info(f"User {call.from_user.id} selected time zone: UTC{'+' if timezone_value > 0 else ''}{timezone_value}")
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
    role_kb = data.get("role", [])
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
    role_kb = data.get("role", [])
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
    F.data.in_(["0-1", "1-3", "3-5", "5-7", "7-10", "боль��е 10"]),
    employer.year_of_exp,
)
async def year_of_exp_selection(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} selected years of experience: {call.data}")
    await state.update_data(year_of_exp=call.data)
    logger.info(f"User {call.from_user.id} is asked to provide vacancy description.")
    await call.message.answer("Описание вакансии (не более 500 символов):", reply_markup=questions_kb)
    await state.set_state(employer.vacancy_description)
    await call.answer()


@router.message(employer.vacancy_description)
async def description(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered vacancy description: {message.text}"
    )
    if len(message.text) > 500:
        await message.answer(
            "Описание вакансии слишком длинное. Пожалуйста, сократите его до 500 символов."
        )
        return
        
    await state.update_data(vacancy_description=message.text)
    await message.answer("Укажите зарплатную вилку:", reply_markup=questions_kb)
    await state.set_state(employer.salary_description)


@router.message(employer.salary_description)
async def salary(message: types.Message, state: FSMContext):
    logger.info(
        f"User {message.from_user.id} entered salary description: {message.text}"
    )
    await state.update_data(salary_description=message.text)
    await message.answer(
        "Укажите ссылку, где можно узнать подробнее о компании:", reply_markup=questions_kb
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
            "Пожалуйста, введите корректную ссылку на сайт компании:"
        )


@router.message(F.text == "подтвердить", employer.confirm)
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
    db.insert_employer(
        data["tg_id"],
        data["company"],
        data["city"],
        time_zone,  # Use the integer time zone value
        data["job_title"],
        data.get("hours", ""),  # Use get with default for optional fields
        data["role"],
        year_of_exp_dict.get(data["year_of_exp"]),
        data["vacancy_description"],
        data["salary_description"],
        data["details"],
    )
    
    logger.info(
        f"User {message.from_user.id} data has been saved to the database with time_zone: {time_zone}"
    )
    
    # Send updated success message
    await message.answer(
        "Спасибо за заявку, теперь вы можете искать себе подходящих кандидатов. "
        "Обратите внимание: бесплатный режим позволяет открывать 3 резюме в день. "
        "Удачи в поиске кандидатов.\n\n"
        "Если вам понадобится помощь, пишите: @natalie_spacehub",
        reply_markup=main_kb
    )
    
    await state.clear()


async def update_on_reject(message: Message, state: FSMContext):
    await state.set_state(employer.confirm)
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
            f"<b>Компания</b>: {data['company']}\n"
            f"<b>Город</b>: {data['city']}\n"
            f"<b>Часовой пояс</b>: {time_zone_display}\n"
            f"<b>Должность</b>: {data['job_title']}\n"
            f"{hours_msg}"
            f"<b>Роли</b>: {roles}\n"
            f"<b>Кол-во лет опыта</b>: {data['year_of_exp']}\n"
            f"<b>Описание вакансии</b>: {data['vacancy_description']}\n"
            f"<b>Зарплатная вилка</b>: {data['salary_description']}\n"
            f"<b>Узнать подробнее</b>: {data['details']}\n"
        ),
        disable_web_page_preview=True,
        parse_mode="HTML",
        reply_markup=confirm_kb,
    )

@router.message(Command("на главное меню"), employer)
async def interrupt_with_main_menu(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} interrupted profile creation with main menu command")
    await state.clear()
    await message.answer("Создание профиля отменено. Вы вернулись в главное меню.", reply_markup=main_kb)

@router.message(Command("отмена"), employer)
async def interrupt_with_cancel(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} interrupted profile creation with cancel command")
    await state.clear()
    await message.answer("Создание профиля отменено.", reply_markup=main_kb)

@router.message(Command("помощь"), employer)
async def help_during_profile(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested help during profile creation")
    current_state = await state.get_state()
    
    await message.answer(
        "Вы находитесь в процессе создания профиля работодателя. "
        "Пожалуйста, следуйте инструкциям бота для заполнения всех полей. "
        "Вы можете использовать команду /отмена, чтобы прервать создание профиля, "
        "или /на_главное_меню, чтобы вернуться в главное меню.",
        reply_markup=None
    )
    
    # Continue with the current state
    state_item = next((item for item in STATE_LIST_EMPLOYER if item.state_name == current_state), None)
    if state_item:
        await message.answer(state_item.state_question, reply_markup=state_item.keyboard)