from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram import types
from aiogram.filters import Command
from all_kb import get_employer_kb, after_respond_kb_2, MyCallback, MyCallback_after
from state_list import find_employee
from handlers.employer_form import employer_selection
from utils import send_vacancy_message, send_not_fully_vacancy_message
from create_bot import bot, db, logger
from datetime import timedelta

router = Router()


@router.message(Command("find_employee"))
@router.message(F.text == "поиск сотрудников")
async def find_employee_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated employee search.")
    if db.get_tg_id_employer(message.from_user.id) is None:
        logger.info(f"User {message.from_user.id} has no employer profile.")
        await message.answer(
            "у вас нет профиля работодателя, давайте заполним данные чтобы вы могли начать поиск"
        )
        await employer_selection(message, state)
        return

    if db.get_end_of_free_week_subscription(message.from_user.id)[0] is not None:
        logger.info(f"User {message.from_user.id} has a free week subscription.")
        await message.answer(
            f"Как новой пользователь у вас доступна бесплатная пробная подписка на 1 неделю до {db.get_end_of_free_week_subscription(message.from_user.id)[0]}"
        )
    elif db.get_end_of_subscription(message.from_user.id)[0] is not None:
        logger.info(f"User {message.from_user.id} has a paid subscription.")
        await message.answer(
            f"У вас активна платная подписка до {db.get_end_of_subscription(message.from_user.id)[0]} (мск)"
        )
    elif db.get_free_vacancies_week(message.from_user.id)[0] >= 1:
        logger.info(f"User {message.from_user.id} has free vacancies left.")
        await message.answer(
            f"На этой неделе у вас осталось {db.get_free_vacancies_week(message.from_user.id)[0]} / 3 бесплатных анкет. Также вы можете купить подписку /pay для безлимитного пользования на 1, 3, 6 месяцев."
        )
    else:
        logger.info(f"User {message.from_user.id} has no free vacancies left.")
        await message.answer(
            "У вас закончились бесплатные анкеты на этой неделе, вы не можете отвечать на вакансии. Вы можете купить платную подписку /pay для безлимитного пользования 1, 3, 6 месяцев."
        )

    await state.set_state(find_employee.get_employee)
    employee_data = db.employer_match(message.from_user.id)
    index = 0
    await state.update_data(employee_data=employee_data, index=index)

    if index < len(employee_data):
        logger.info(f"User {message.from_user.id} found matching vacancies.")
        await message.answer("подходящие вам вакансии", reply_markup=get_employer_kb)
    else:
        logger.info(f"User {message.from_user.id} found no matching vacancies.")
        await message.answer("На данный момент вакансий нет")
        return

    if db.get_end_of_free_week_subscription(message.from_user.id)[0] is not None:
        if (
            message.date.replace(tzinfo=None) + timedelta(hours=3)
            <= db.get_end_of_free_week_subscription(message.from_user.id)[0]
        ):
            await send_vacancy_message(
                message, employee_data, index, state=await state.get_state()
            )

    elif db.get_end_of_subscription(message.from_user.id)[0] is not None:
        if (
            message.date.replace(tzinfo=None) + timedelta(hours=3)
            <= db.get_end_of_subscription(message.from_user.id)[0]
        ):
            await send_vacancy_message(
                message, employee_data, index, state=await state.get_state()
            )

    elif db.get_free_vacancies_week(message.from_user.id)[0] >= 1:
        await send_vacancy_message(
            message, employee_data, index, state=await state.get_state()
        )
        db.subtract_free_vacancies(message.from_user.id)
    else:
        await send_not_fully_vacancy_message(message, employee_data, index)


@router.message(F.text == "далее", find_employee.get_employee)
async def find_job_next_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    employee_data = data.get("employee_data", [])
    index = data.get("index", 0) + 1

    if db.get_end_of_free_week_subscription(message.from_user.id)[0] is not None:
        if (
            message.date.replace(tzinfo=None) + timedelta(hours=3)
            <= db.get_end_of_free_week_subscription(message.from_user.id)[0]
        ):
            if index < len(employee_data):
                logger.info(
                    f"User {message.from_user.id} viewing next job, index {index}."
                )
                await state.update_data(index=index)
                await send_vacancy_message(
                    message, employee_data, index, state=await state.get_state()
                )
            else:
                logger.info(f"User {message.from_user.id} has no more jobs to view.")
                await message.answer("Больше вакансий нет.")

    elif db.get_end_of_subscription(message.from_user.id)[0] is not None:
        if (
            message.date.replace(tzinfo=None) + timedelta(hours=3)
            <= db.get_end_of_subscription(message.from_user.id)[0]
        ):
            if index < len(employee_data):
                logger.info(
                    f"User {message.from_user.id} viewing next job, index {index}."
                )
                await state.update_data(index=index)
                await send_vacancy_message(
                    message, employee_data, index, state=await state.get_state()
                )
            else:
                logger.info(f"User {message.from_user.id} has no more jobs to view.")
                await message.answer("Больше вакансий нет.")

    elif db.get_free_vacancies_week(message.from_user.id)[0] >= 1:
        if index < len(employee_data):
            logger.info(f"User {message.from_user.id} viewing next job, index {index}.")
            await state.update_data(index=index)
            await send_vacancy_message(
                message, employee_data, index, state=await state.get_state()
            )
            db.subtract_free_vacancies(message.from_user.id)
        else:
            logger.info(f"User {message.from_user.id} has no more jobs to view.")
            await message.answer("Больше вакансий нет.")

    else:
        if index < len(employee_data):
            logger.info(f"User {message.from_user.id} viewing next job, index {index}.")
            await state.update_data(index=index)
            await send_not_fully_vacancy_message(message, employee_data, index)
        else:
            logger.info(f"User {message.from_user.id} has no more jobs to view.")
            await message.answer("Больше вакансий нет.")


@router.callback_query(
    MyCallback.filter(F.path == "respond"), find_employee.get_employee
)
async def respond_employer_handler(
    call: types.CallbackQuery, state: FSMContext, callback_data: MyCallback
):
    logger.info(f"User {call.from_user.id} responded to a vacancy.")
    db.set_match(callback_data.user_tg_id, call.from_user.id, call.from_user.id)
    employer_data = db.get_employer(call.from_user.id)
    hours = (
        f"<b>Количество часов</b>:{employer_data[5]}\n"
        if employer_data[5] != ""
        else ""
    )
    await bot.send_message(
        chat_id=callback_data.user_tg_id,
        text=(
            "С вами хочет связаться работодатель."
            f"<b>Компания</b>: {employer_data[1]}\n"
            f"<b>Город</b>: {employer_data[2]}\n"
            f"<b>Часовой пояс</b>: {employer_data[3]}\n"
            f"<b>Должность</b>: {employer_data[4]}\n"
            f"{hours}"
            f"<b>Роли</b>:{employer_data[6]}\n"
            f"<b>Кол-во лет опыта</b>: {employer_data[7]}\n"
            f"<b>Описание вакансии</b>: {employer_data[8]}\n"
            f"<b>Зарплатная ветка</b>: {employer_data[9]}\n"
            f"<b>Узнать подробнее</b>: {employer_data[10]}\n"
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="связаться",
                        callback_data=MyCallback_after(
                            path="contact",
                            employer_tg_id=call.from_user.id,
                            employee_tg_id=callback_data.user_tg_id,
                            username=call.from_user.username,
                            state=(await state.get_state()).split(":")[0],
                        ).pack(),
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="отклонить",
                        callback_data=MyCallback_after(
                            path="reject",
                            employer_tg_id=call.from_user.id,
                            employee_tg_id=callback_data.user_tg_id,
                            username=call.from_user.username,
                            state=(await state.get_state()).split(":")[0],
                        ).pack(),
                    )
                ],
            ]
        ),
    )
    await call.message.edit_reply_markup(reply_markup=after_respond_kb_2)
    await call.answer()
