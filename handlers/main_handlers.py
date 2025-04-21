from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram import types
from all_kb import choose_role_kb, main_kb, employer_main_kb, MyCallback_after, contact_kb, reject_kb
from state_list import STATE_LIST_EMPLOYEE, STATE_LIST_EMPLOYER
from create_bot import bot, db, router, logger

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    logger.info(f"Received /start command from user {message.from_user.id}")
    db.insert_tg_id_into_user(message.from_user.id)
    await message.answer(
        """👋 Добро пожаловать в BusyBeaver-бот от SpaceHub!

🔍 Этот бот поможет вам быстро найти работу или подходящих сотрудников, работая по принципу Тиндера.

📝 Что умеет бот:
• Для соискателей: создание профиля, поиск вакансий, отклики на интересные предложения
• Для работодателей: создание вакансий, поиск кандидатов, управление откликами

🚀 Начните с выбора вашей роли и заполнения профиля. Затем вы сможете искать вакансии или сотрудников!

❓ Если у вас возникнут вопросы, используйте кнопку "помощь и обратная связь".

Выберите вашу роль:""",
        reply_markup=choose_role_kb,
        disable_web_page_preview=True,
    )


@router.message(Command("отмена"))
@router.message(F.text == "отмена")
async def cancel_handler(message: Message, state: FSMContext):
    logger.info(f"Received /отмена command from user {message.from_user.id}")
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    
    # Check if user is an employer
    is_employer = db.get_tg_id_employer(message.from_user.id) is not None
    keyboard = employer_main_kb if is_employer else main_kb
    
    await message.answer("Отменено.", reply_markup=keyboard)


def get_previous_state(current_state: str, state_list: list) -> str:
    current_state_index = next(
        (i for i, obj in enumerate(state_list) if obj.state_name == current_state),
        None,
    )
    previous_state_index = current_state_index - 1
    if previous_state_index < 0:
        return None, None
    return (
        state_list[previous_state_index].state_name,
        state_list[previous_state_index].state_question,
        state_list[previous_state_index].keyboard,
    )


@router.message(Command("назад"))
@router.message(F.text == "назад")
async def go_back_handler(message: Message, state: FSMContext) -> None:
    logger.info(f"Received /назад command from user {message.from_user.id}")
    data = await state.get_data()
    current_state = await state.get_state()
    if not current_state:
        return
    if current_state.split(":")[0] == "employee":
        state_list = STATE_LIST_EMPLOYEE
    else:
        state_list = STATE_LIST_EMPLOYER
    (previous_state, state_message, keyboard) = get_previous_state(
        current_state, state_list
    )

    if (
        "job_title" in data
        and data["job_title"] == "фулл-тайм"
        and current_state == "employee:role"
    ):
        (previous_state, state_message, keyboard) = get_previous_state(
            previous_state, state_list
        )
    if callable(keyboard):
        role_data = data.get("role", [])
        keyboard = keyboard(role_data)
    if previous_state is None:
        await message.answer(
            "Вы уже на первом вопросе.",
        )
    else:
        await state.set_state(previous_state)
        await message.answer(state_message, reply_markup=keyboard)


@router.message(Command("на главное меню"))
@router.message(F.text == "на главное меню")
async def go_back_to_main_menu_handler(message: Message, state: FSMContext):
    logger.info(f"Received /на главное меню command from user {message.from_user.id}")
    
    # Check if user is an employer
    is_employer = db.get_tg_id_employer(message.from_user.id) is not None
    keyboard = employer_main_kb if is_employer else main_kb
    
    await message.answer("Вернулись на главное меню.", reply_markup=keyboard)
    await state.clear()


@router.callback_query(MyCallback_after.filter(F.path == "contact"))
async def respond_message_handler(
    call: types.CallbackQuery, callback_data: MyCallback_after
):
    logger.info(f"Received contact callback from user {call.from_user.id}")
    if callback_data.state == "find_employee":
        db.set_match_result_true(
            callback_data.employee_tg_id,
            callback_data.employer_tg_id,
            callback_data.employer_tg_id,
        )
        await call.message.edit_reply_markup(reply_markup=contact_kb)
        await call.message.answer(f"Телеграмм работодателя:@{callback_data.username}")
        await bot.send_message(
            chat_id=callback_data.employer_tg_id,
            text=f"Взаимный ответ, с вами хочет связаться соискатель:@{call.from_user.username}",
        )
    else:
        if db.get_end_of_free_week_subscription(call.from_user.id)[0] != None:
            db.set_match_result_true(
                callback_data.employee_tg_id,
                callback_data.employee_tg_id,
                callback_data.employer_tg_id,
            )
            await call.message.edit_reply_markup(reply_markup=contact_kb)
            await call.message.answer(f"Телеграмм соискателя:@{callback_data.username}")
            await bot.send_message(
                chat_id=callback_data.employee_tg_id,
                text=f"Взаимный ответ, с вами хочет связаться работодатель:@{call.from_user.username}",
            )
        elif db.get_end_of_subscription(call.from_user.id)[0] != None:
            db.set_match_result_true(
                callback_data.employee_tg_id,
                callback_data.employee_tg_id,
                callback_data.employer_tg_id,
            )
            await call.message.edit_reply_markup(reply_markup=contact_kb)
            await call.message.answer(f"Телеграмм соискателя:@{callback_data.username}")
            await bot.send_message(
                chat_id=callback_data.employee_tg_id,
                text=f"Взаимный ответ, с вами хочет связаться работодатель:@{call.from_user.username}",
            )
        elif db.get_free_vacancies_week(call.from_user.id)[0] >= 1:
            db.set_match_result_true(
                callback_data.employee_tg_id,
                callback_data.employee_tg_id,
                callback_data.employer_tg_id,
            )
            await call.message.edit_reply_markup(reply_markup=contact_kb)
            await call.message.answer(f"Телеграмм соискателя:@{callback_data.username}")
            await bot.send_message(
                chat_id=callback_data.employee_tg_id,
                text=f"Взаимный ответ, с вами хочет связаться работодатель:@{call.from_user.username}",
            )
            db.subtract_free_vacancies(call.from_user.id)
        else:
            await call.message.answer(
                "У вас закончились бесплатные анкеты на этой неделе, вы не можете отвечать на вакансии. Вы можете купить платную подписку по кнопке 'подписка' для безлимитного пользования"
            )
        await call.answer()


@router.callback_query(MyCallback_after.filter(F.path == "reject"))
async def respond_message_handler(
    call: types.CallbackQuery, callback_data: MyCallback_after
):
    logger.info(f"Received reject callback from user {call.from_user.id}")
    if callback_data.state == "find_employee":
        db.set_match_result_false(
            callback_data.employee_tg_id,
            callback_data.employer_tg_id,
            callback_data.employer_tg_id,
        )
        await call.message.edit_reply_markup(reply_markup=reject_kb)
    else:
        db.set_match_result_false(
            callback_data.employee_tg_id,
            callback_data.employee_tg_id,
            callback_data.employer_tg_id,
        )
        await call.message.edit_reply_markup(reply_markup=reject_kb)
    await call.answer()

@router.message(F.text == "помощь и обратная связь")
async def help_and_feedback_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested help and feedback information.")
    
    # Check if user is an employer
    is_employer = db.get_tg_id_employer(message.from_user.id) is not None
    
    if is_employer:
        help_text = (
            "Busybeaver бот: найди сотрудника за час без откликов, долгих согласований и перебора резюме\n\n"
            "• Не нужно мониторить сайты для поиска работы, все работает прямо в Telegram\n"
            "• Не нужно оформлять вакансию на сайте, просто заполни свой профиль, и соискатели свяжутся с тобой напрямую\n"
            "• Получай отклики только от тех, кто подходит под твой запрос, не нужно перебирать тонны резюме\n"
            "• Не нужно тратить время на множество этапов – размещение вакансии, отбор резюме, отклики, ответы соискателям, звонки, собеседования в Zoom\n"
            "• На hh.ru размещение одной вакансии стоит до 10000 рублей, и отдельно за каждый клик на вакансии, в BusyBeaver количество откликов неограниченно\n\n"
            "Бот работает по принципу Тиндера:\n"
            "1. Запусти бот и заполни свой профиль за несколько простых шагов\n"
            "2. Бот сразу предложит тебе 5 кандидатов, соответствующих твоему запросу\n"
            "3. Нажми \"Откликнуться\" или \"Показать ещё\"\n"
            "4. Соискатель видит твой отклик у себя и принимает его – ваши анкеты \"мэтчатся\", и бот передает вам контакты друг друга\n\n"
            "За саппортом пиши сюда: @natalie_spacehub"
        )
    else:
        help_text = (
            "Busy beaver бот: найди работу за час без откликов, долгих согласований и поиска вакансии\n\n"
            "• Не нужно мониторить сайты для поиска работы, все работает прямо в Telegram\n"
            "• Не нужно оформлять резюме на сайте, просто заполни свой профиль, и работодатели свяжутся с тобой напрямую\n"
            "• Получай отклики только от тех, кто подходит под твой запрос, не нужно перебирать тонны вакансий\n"
            "• Не нужно тратить время на множество этапов – размещение резюме, поиск вакансий, отклики, ответы рекрутерам, звонки, собеседования в Zoom\n"
            "• Это БЕСПЛАТНО\n\n"
            "Бот работает по принципу Тиндера:\n"
            "1. Запусти бот и заполни свой профиль за несколько простых шагов\n"
            "2. Бот сразу предложит тебе 5 вакансий, соответствующих твоему профилю\n"
            "3. Нажми \"Откликнуться\" или \"Показать ещё\"\n"
            "4. Работодатель видит твой отклик у себя и принимает его – ваши анкеты \"мэтчатся\", и бот передает вам прямые контакты друг друга\n\n"
            "За саппортом пиши сюда: @natalie_spacehub"
        )
    
    keyboard = employer_main_kb if is_employer else main_kb
    await message.answer(help_text, reply_markup=keyboard)