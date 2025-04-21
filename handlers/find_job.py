from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from all_kb import get_employer_kb, main_kb, MyCallback, MyCallback_after
from state_list import find_job
from create_bot import db, logger
from utils import send_vacancy_message
from aiogram import types

router = Router()


@router.message(Command("поиск работы"))
@router.message(F.text == "поиск работы")
async def find_job_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated job search.")
    if db.get_tg_id_employee(message.from_user.id) is not None:
        await state.set_state(find_job.get_job)
        await state.update_data(index=0)
        data = db.employee_match(message.from_user.id)
        if len(data) > 0:
            await send_vacancy_message(message, data, 0, "find_job:get_job")
        else:
            await message.answer(
                "К сожалению, подходящих вакансий не найдено. Попробуйте изменить параметры в своем профиле или проверить позже.",
                reply_markup=main_kb
            )
            await state.clear()
    else:
        logger.warning(f"User {message.from_user.id} has no employee profile for job search.")
        await message.answer(
            "У вас нет анкеты соискателя. Пожалуйста, заполните профиль, чтобы начать поиск работы.",
            reply_markup=main_kb
        )


@router.message(F.text == "далее", find_job.get_job)
async def next_job_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested next job.")
    data = await state.get_data()
    index = data.get("index", 0) + 1
    await state.update_data(index=index)
    
    employer_data = db.employee_match(message.from_user.id)
    if len(employer_data) > index:
        await send_vacancy_message(message, employer_data, index, "find_job:get_job")
    else:
        await message.answer(
            "Вы просмотрели все доступные вакансии. Возвращайтесь позже, чтобы увидеть новые предложения.",
            reply_markup=main_kb
        )
        await state.clear()


@router.callback_query(MyCallback.filter(F.path == "respond"))
async def respond_handler(call: CallbackQuery, callback_data: MyCallback, state: FSMContext):
    logger.info(f"User {call.from_user.id} clicked respond button for user {callback_data.user_tg_id}")
    
    current_state = await state.get_state()
    if current_state == "find_job:get_job":
        # Employee responding to employer
        employee_tg_id = call.from_user.id
        employer_tg_id = callback_data.user_tg_id
        
        try:
            # Check if already responded
            employer_data = db.employee_match(employee_tg_id)
            for data in employer_data:
                if data[0] == employer_tg_id and data[12] is not None:
                    await call.answer("Вы уже откликнулись на эту вакансию.", show_alert=True)
                    return
                    
            # Set match in database
            db.set_match(employee_tg_id, employee_tg_id, employer_tg_id)
            
            # Get employer username
            employer_username = await call.bot.get_chat(employer_tg_id)
            username = employer_username.username if employer_username.username else "без username"
            
            # Notify employer about new response
            await call.bot.send_message(
                chat_id=employer_tg_id,
                text=f"На вашу вакансию откликнулся соискатель: @{call.from_user.username or 'без username'}",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="Связаться",
                        callback_data=MyCallback_after(
                            path="contact",
                            employer_tg_id=employer_tg_id,
                            employee_tg_id=employee_tg_id,
                            username=call.from_user.username or "без username",
                            state="find_employee"
                        ).pack()
                    )],
                    [types.InlineKeyboardButton(
                        text="Отклонить",
                        callback_data=MyCallback_after(
                            path="reject",
                            employer_tg_id=employer_tg_id,
                            employee_tg_id=employee_tg_id,
                            username=call.from_user.username or "без username",
                            state="find_employee"
                        ).pack()
                    )]
                ])
            )
            
            # Confirm to user
            await call.answer("Ваш отклик успешно отправлен работодателю!", show_alert=True)
            await call.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Вы откликнулись ✅", callback_data="already_responded")]
            ]))
            
        except Exception as e:
            logger.error(f"Error in respond_handler: {e}")
            await call.answer("Произошла ошибка при отправке отклика. Пожалуйста, попробуйте позже.", show_alert=True)
    
    elif current_state == "find_employee:get_employee":
        # Employer responding to employee
        employer_tg_id = call.from_user.id
        employee_tg_id = callback_data.user_tg_id
        
        try:
            # Check subscription status
            if db.get_end_of_free_week_subscription(employer_tg_id)[0] is None and \
               db.get_end_of_subscription(employer_tg_id)[0] is None and \
               db.get_free_vacancies_week(employer_tg_id)[0] < 1:
                await call.answer(
                    "У вас закончились бесплатные отклики на этой неделе. Приобретите подписку для неограниченного доступа.",
                    show_alert=True
                )
                return
                
            # Check if already responded
            employee_data = db.employer_match(employer_tg_id)
            for data in employee_data:
                if data[0] == employee_tg_id and data[12] is not None:
                    await call.answer("Вы уже откликнулись на этого кандидата.", show_alert=True)
                    return
            
            # Set match in database
            db.set_match(employee_tg_id, employer_tg_id, employer_tg_id)
            
            # Subtract free vacancy if applicable
            if db.get_end_of_free_week_subscription(employer_tg_id)[0] is None and \
               db.get_end_of_subscription(employer_tg_id)[0] is None:
                db.subtract_free_vacancies(employer_tg_id)
            
            # Get employee username
            employee_username = await call.bot.get_chat(employee_tg_id)
            username = employee_username.username if employee_username.username else "без username"
            
            # Notify employee about new response
            await call.bot.send_message(
                chat_id=employee_tg_id,
                text=f"Работодатель заинтересовался вашим профилем: @{call.from_user.username or 'без username'}",
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="Связаться",
                        callback_data=MyCallback_after(
                            path="contact",
                            employer_tg_id=employer_tg_id,
                            employee_tg_id=employee_tg_id,
                            username=call.from_user.username or "без username",
                            state="find_job"
                        ).pack()
                    )],
                    [types.InlineKeyboardButton(
                        text="Отклонить",
                        callback_data=MyCallback_after(
                            path="reject",
                            employer_tg_id=employer_tg_id,
                            employee_tg_id=employee_tg_id,
                            username=call.from_user.username or "без username",
                            state="find_job"
                        ).pack()
                    )]
                ])
            )
            
            # Confirm to user
            await call.answer("Ваш отклик успешно отправлен соискателю!", show_alert=True)
            await call.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Вы откликнулись ✅", callback_data="already_responded")]
            ]))
            
        except Exception as e:
            logger.error(f"Error in respond_handler: {e}")
            await call.answer("Произошла ошибка при отправке отклика. Пожалуйста, попробуйте позже.", show_alert=True)
    
    else:
        await call.answer("Невозможно откликнуться в текущем состоянии. Вернитесь в меню поиска.", show_alert=True)