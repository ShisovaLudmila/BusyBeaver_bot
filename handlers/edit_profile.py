from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import types
import re
from all_kb import (
    get_data_kb,
    main_kb,
    change_employee_kb_1,
    change_employee_kb_2,
    change_employer_kb_1,
    change_employer_kb_2,
    change_keyboard_time_zone,
    create_role_kb,
    first_question_kb,
    questions_kb,
)
from state_list import (
    edit_employee,
    edit_employer,
    STATE_LIST_EMPLOYEE,
    STATE_LIST_EMPLOYER,
)
from create_bot import db, logger
from validation import validate_input_employee
from handlers.employee_form import year_of_exp_dict

router = Router()


@router.message(Command("edit profile"))
@router.message(F.text == "редактировать профиль")
async def edit_profile_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested profile selection")
    await message.answer(
        "Выберите какой из профилей вы хотите измненить", reply_markup=get_data_kb
    )


@router.message(Command("для соискателя"))
@router.message(F.text == "для соискателя")
async def edit_employee_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested employee profile")
    if db.get_tg_id_employee(message.from_user.id) != None:
        user_data = db.get_employee(message.from_user.id)
        hours = (
            f"<b>Количество часов</b>:{user_data[7]}\n" if user_data[7] != "" else ""
        )
        await message.answer(
            (
                "Какие данные ты вы хотите изменить?"
                f"Ваша анкета соискателя:\n"
                f"<b>Имя</b>: {user_data[1]}\n"
                f"<b>Фамилия</b>: {user_data[2]}\n"
                f"<b>Дата рождения</b>: {user_data[3]}\n"
                f"<b>Город</b>: {user_data[4]}\n"
                f"<b>Часовой пояс</b>: {user_data[5]}\n"
                f"<b>Должность</b>: {user_data[6]}\n"
                f"{hours}"
                f"<b>Роли</b>:{user_data[8]}\n"
                f"<b>Кол-во лет опыта</b>: {user_data[9]}\n"
                f"<b>Резюме</b>: {user_data[10]}\n"
                f"<b>Видеовизитка</b>: {user_data[11]}\n"
            ),
            parse_mode="HTML",
            reply_markup=(
                change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
            ),
        )
        await state.set_state(edit_employee.choose_field)
    else:
        logger.warning(f"User {message.from_user.id} has no employee profile")
        await message.answer("у вас нет анкеты для соискателя", reply_markup=main_kb)


@router.message(edit_employee.choose_field)
async def choose_name(message: Message, state: FSMContext):
    chosen_field = message.text

    for state_item in STATE_LIST_EMPLOYEE:
        if state_item.state_corresponding_button == chosen_field:
            await state.update_data(state_item=state_item)
            await state.set_state(edit_employee.update_value)
            if state_item.keyboard == questions_kb:
                await message.answer(
                    state_item.state_question, reply_markup=first_question_kb
                )
            else:
                await message.answer(
                    state_item.state_question, reply_markup=state_item.keyboard
                )


# хэндлер для всех текстовых ответов
@router.message(edit_employee.update_value)
async def update_value(message: Message, state: FSMContext):
    user_data = db.get_employee(message.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = message.text

    # Проверка корректности введённых данных
    if not validate_input_employee(field_to_update, value):

        if data["state_item"].keyboard == questions_kb:
            await message.answer(
                data["state_item"].state_question + " повторно:",
                reply_markup=first_question_kb,
            )
        else:
            await message.answer(
                data["state_item"].state_question + " повторно:",
                reply_markup=data["state_item"].keyboard,
            )
        return

    # Если данные корректные, обновляем их в базе данных
    db.change_employee_field(field_to_update, value, message.from_user.id)
    await message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


# сделаем обработчик каллбеков для инлайн кнопков вызываемых при редактировании
# обработка для часового пояс
@router.callback_query(
    F.data.in_(["decrease", "increase"]),
    edit_employee.update_value,
)
async def callback_change_timezone(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    timezone_value = data.get("time_zone", 0)

    if call.data == "increase" and timezone_value < 14:
        timezone_value += 1
    elif call.data == "decrease" and timezone_value > -12:
        timezone_value -= 1

    await state.update_data(time_zone=timezone_value)

    keyboard = change_keyboard_time_zone(timezone_value)
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(
    F.data == "time_zone_callback",
    edit_employee.update_value,
)
async def callback_timezone_selection(call: types.CallbackQuery, state: FSMContext):

    user_data = db.get_employee(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = data["time_zone"]

    db.change_employee_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


# обработчик каллбэеов для должностей
@router.callback_query(F.data == "фулл-тайм", edit_employee.update_value)
async def job_title_selection_full_time(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employee(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employee_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


@router.callback_query(F.data == "парт-тайм", edit_employee.update_value)
async def job_title_selection_part_time(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employee(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employee_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


@router.callback_query(F.data == "оба варианта", edit_employee.update_value)
async def job_title_selection_both(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employee(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employee_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


@router.callback_query(
    F.data.in_(["1", "2", "3", "4", "5", "6", "7"]), edit_employee.update_value
)
async def hours_selection(call: types.CallbackQuery, state: FSMContext):

    user_data = db.get_employee(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employee_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


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
    edit_employee.update_value,
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
        user_data = db.get_employee(call.from_user.id)
        data = await state.get_data()
        field_to_update = data["state_item"].state_in_memory_name
        value = ", ".join(role_data)

        db.change_employee_field(field_to_update, value, call.from_user.id)

        await call.message.answer(
            "Изменили",
            reply_markup=(
                change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
            ),
        )

        await state.set_state(edit_employee.choose_field)


@router.callback_query(
    F.data.in_(["0-1", "1-3", "3-5", "5-7", "7-10", "больше 10"]),
    edit_employee.update_value,
)
async def year_of_exp_selection(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employee(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = year_of_exp_dict.get(call.data)

    db.change_employee_field(field_to_update, value, call.from_user.id)
    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employee_kb_1 if user_data[7] != "" else change_employee_kb_2
        ),
    )

    await state.set_state(edit_employee.choose_field)


@router.message(Command("для работодателя"))
@router.message(F.text == "для работодателя")
async def get__employer_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested employer profile")
    if db.get_tg_id_employer(message.from_user.id) != None:
        user_data = db.get_employer(message.from_user.id)
        hours = (
            f"<b>Количество часов</b>:{user_data[5]}\n" if user_data[5] != "" else ""
        )
        await message.answer(
            (
                "Какие данные ты вы хотите изменить?"
                f"Ваша вакансия работодателя:\n"
                f"<b>Компания</b>: {user_data[1]}\n"
                f"<b>Город</b>: {user_data[2]}\n"
                f"<b>Часовой пояс</b>: {user_data[3]}\n"
                f"<b>Должность</b>: {user_data[4]}\n"
                f"{hours}"
                f"<b>Роли</b>:{user_data[6]}\n"
                f"<b>Кол-во лет опыта</b>: {user_data[7]}\n"
                f"<b>Описание вакансии</b>: {user_data[8]}\n"
                f"<b>Зарплатная ветка</b>: {user_data[9]}\n"
                f"<b>Узнать подробнее</b>: {user_data[10]}\n"
            ),
            parse_mode="HTML",
            reply_markup=(
                change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
            ),
        )
        await state.set_state(edit_employer.choose_field)

    else:
        logger.warning(f"User {message.from_user.id} has no employer profile")
        await message.answer("У вас нет анкеты для работадателя", reply_markup=main_kb)


@router.message(edit_employer.choose_field)
async def choose_name(message: Message, state: FSMContext):
    chosen_field = message.text

    for state_item in STATE_LIST_EMPLOYER:
        if state_item.state_corresponding_button == chosen_field:
            await state.update_data(state_item=state_item)
            await state.set_state(edit_employer.update_value)
            if state_item.keyboard == questions_kb:
                await message.answer(
                    state_item.state_question, reply_markup=first_question_kb
                )
            else:
                await message.answer(
                    state_item.state_question, reply_markup=state_item.keyboard
                )


@router.message(edit_employer.update_value)
async def update_value(message: Message, state: FSMContext):
    user_data = db.get_employer(message.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = message.text

    if field_to_update == "details":
        if not re.fullmatch(
            r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$", value
        ):
            if data["state_item"].keyboard == questions_kb:
                await message.answer(
                    data["state_item"].state_question + " повторно :",
                    reply_markup=first_question_kb,
                )
            else:
                await message.answer(
                    data["state_item"].state_question + " повторно :",
                    reply_markup=data["state_item"].keyboard,
                )
            return

    db.change_employer_field(field_to_update, value, message.from_user.id)
    await message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)


@router.callback_query(
    F.data.in_(["decrease", "increase"]),
    edit_employer.update_value,
)
async def callback_change_timezone(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    timezone_value = data.get("time_zone", 0)

    if call.data == "increase" and timezone_value < 14:
        timezone_value += 1
    elif call.data == "decrease" and timezone_value > -12:
        timezone_value -= 1

    await state.update_data(time_zone=timezone_value)

    keyboard = change_keyboard_time_zone(timezone_value)
    await call.message.edit_reply_markup(reply_markup=keyboard)
    await call.answer()


@router.callback_query(
    F.data == "time_zone_callback",
    edit_employer.update_value,
)
async def callback_timezone_selection(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employer(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = data["time_zone"]

    db.change_employer_field(field_to_update, value, call.from_user.id)
    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)


@router.callback_query(F.data == "фулл-тайм", edit_employer.update_value)
async def job_title_selection_full_time(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employer(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employer_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)


@router.callback_query(F.data == "парт-тайм", edit_employer.update_value)
async def job_title_selection_part_time(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employer(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employer_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)


@router.callback_query(F.data == "оба варианта", edit_employer.update_value)
async def job_title_selection_both(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employer(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employer_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)


@router.callback_query(
    F.data.in_(["1", "2", "3", "4", "5", "6", "7"]), edit_employer.update_value
)
async def hours_selection(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employer(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = call.data

    db.change_employer_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)


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
    edit_employer.update_value,
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
        user_data = db.get_employer(call.from_user.id)
        data = await state.get_data()
        field_to_update = data["state_item"].state_in_memory_name
        value = ", ".join(role_data)

        db.change_employer_field(field_to_update, value, call.from_user.id)

        await call.message.answer(
            "Изменили",
            reply_markup=(
                change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
            ),
        )

        await state.set_state(edit_employer.choose_field)


@router.callback_query(
    F.data.in_(["0-1", "1-3", "3-5", "5-7", "7-10", "больше 10"]),
    edit_employer.update_value,
)
async def year_of_exp_selection(call: types.CallbackQuery, state: FSMContext):
    user_data = db.get_employer(call.from_user.id)
    data = await state.get_data()
    field_to_update = data["state_item"].state_in_memory_name
    value = year_of_exp_dict.get(call.data)

    db.change_employer_field(field_to_update, value, call.from_user.id)

    await call.message.answer(
        "Изменили",
        reply_markup=(
            change_employer_kb_1 if user_data[5] != "" else change_employer_kb_2
        ),
    )

    await state.set_state(edit_employer.choose_field)
