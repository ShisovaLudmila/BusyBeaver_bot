from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup , CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram import types
from aiogram.filters import Command
from all_kb import get_employer_kb, after_respond_kb_2, MyCallback, MyCallback_after , main_kb
from state_list import find_employee
from handlers.employer_form import employer_selection
from utils import send_vacancy_message, send_not_fully_vacancy_message
from create_bot import bot, db, logger
from datetime import timedelta
from send_not_full_vacancy_message import send_not_fully_vacancy_message
router = Router()
from datetime import datetime

@router.message(Command("поиск сотрудников"))
@router.message(F.text == "поиск сотрудников")
async def find_employee_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated employee search.")
    
    # Debug logging to check employer profile
    employer_profile = db.get_tg_id_employer(message.from_user.id)
    logger.info(f"Employer profile check result: {employer_profile}")
    
    if employer_profile is not None:
        await state.set_state(find_employee.get_employee)
        await state.update_data(index=0)
        
        # Get matching employees
        employee_data = db.employer_match(message.from_user.id)
        logger.info(f"Found {len(employee_data)} matching employees for employer {message.from_user.id}")
        
        if len(employee_data) > 0:
            # Check subscription status
            if db.get_end_of_free_week_subscription(message.from_user.id)[0] is not None:
                # Free week subscription
                await send_vacancy_message(message, employee_data, 0, "find_employee:get_employee")
            elif db.get_end_of_subscription(message.from_user.id)[0] is not None:
                # Paid subscription
                await send_vacancy_message(message, employee_data, 0, "find_employee:get_employee")
            elif db.get_free_vacancies_week(message.from_user.id)[0] >= 1:
                # Has free vacancies left
                await send_vacancy_message(message, employee_data, 0, "find_employee:get_employee")
            else:
                # No subscription or free vacancies
                await send_not_fully_vacancy_message(message, employee_data, 0)
                await message.answer(
                    "У вас закончились бесплатные просмотры на этой неделе. Приобретите подписку для неограниченного доступа.",
                    reply_markup=main_kb
                )
                await state.clear()
        else:
            await message.answer(
                "К сожалению, подходящих кандидатов не найдено. Попробуйте изменить параметры в своем профиле или проверить позже.",
                reply_markup=main_kb
            )
            await state.clear()
    else:
        logger.warning(f"User {message.from_user.id} has no employer profile for employee search.")
        await message.answer(
            "У вас нет анкеты работодателя. Пожалуйста, заполните профиль, чтобы начать поиск сотрудников.",
            reply_markup=main_kb
        )



@router.message(F.text == "далее", find_employee.get_employee)
async def next_employee_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested next employee.")
    data = await state.get_data()
    index = data.get("index", 0) + 1
    await state.update_data(index=index)
    
    employee_data = db.employer_match(message.from_user.id)
    if len(employee_data) > index:
        # Check subscription status
        if db.get_end_of_free_week_subscription(message.from_user.id)[0] is not None:
            # Free week subscription
            await send_vacancy_message(message, employee_data, index, "find_employee:get_employee")
        elif db.get_end_of_subscription(message.from_user.id)[0] is not None:
            # Paid subscription
            await send_vacancy_message(message, employee_data, index, "find_employee:get_employee")
        elif db.get_free_vacancies_week(message.from_user.id)[0] >= 1:
            # Has free vacancies left
            await send_vacancy_message(message, employee_data, index, "find_employee:get_employee")
        else:
            # No subscription or free vacancies
            await send_not_fully_vacancy_message(message, employee_data, index)
            await message.answer(
                "У вас закончились бесплатные просмотры на этой неделе. Приобретите подписку для неограниченного доступа.",
                reply_markup=main_kb
            )
            await state.clear()
    else:
        await message.answer(
            "Вы просмотрели всех доступных кандидатов. Возвращайтесь позже, чтобы увидеть новые профили.",
            reply_markup=main_kb
        )
        await state.clear()


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
