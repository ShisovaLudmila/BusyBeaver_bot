from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram import types
from all_kb import get_employer_kb, after_respond_kb_1, MyCallback, MyCallback_after
from state_list import find_job
from handlers.employee_form import employee_selection
from utils import send_vacancy_message
from create_bot import bot, db, logger

router = Router()

@router.message(Command("find_job"))
@router.message(F.text == "поиск работы")
async def find_job_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} initiated job search.")
    await state.set_state(find_job.get_job)
    if db.get_tg_id_employee(message.from_user.id) is None:
        logger.info(f"User {message.from_user.id} has no employee profile.")
        await message.answer("у вас нет профиля соискателя, давайте заполним данные чтобы вы могли начать поиск")
        await employee_selection(message, state)
    else:
        index = 0
        employer_data = db.employee_match(message.from_user.id)
        await state.update_data(employer_data=employer_data, index=index)
        
        if index < len(employer_data):
            logger.info(f"User {message.from_user.id} found matching jobs.")
            await message.answer("подходящие вам вакансии", reply_markup=get_employer_kb)
            await send_vacancy_message(message, employer_data, index, state=await state.get_state())
        else:
            logger.info(f"User {message.from_user.id} found no matching jobs.")
            await message.answer("На данный момент вакансий нет")
            return
        
@router.message(F.text == "далее", find_job.get_job)
async def find_job_next_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    employer_data = data.get('employer_data', [])
    index = data.get('index', 0) + 1
    
    if index < len(employer_data):
        logger.info(f"User {message.from_user.id} is viewing next job, index {index}.")
        await state.update_data(index=index)
        await send_vacancy_message(message, employer_data, index, state=await state.get_state())
    else:
        logger.info(f"User {message.from_user.id} has no more jobs to view.")
        await message.answer("Больше вакансий нет.")
                    
@router.callback_query(MyCallback.filter(F.path == "respond"), find_job.get_job)
async def respond_employer_handler(call: types.CallbackQuery, state: FSMContext, callback_data: MyCallback):
    logger.info(f"User {call.from_user.id} responded to a job.")
    db.set_match(call.from_user.id, call.from_user.id, callback_data.user_tg_id)
    employee_data = db.get_employee(call.from_user.id)
    hours = f"<b>Количество часов</b>:{employee_data[7]}\n" if employee_data[7] != "" else ""
    await bot.send_message(chat_id=callback_data.user_tg_id, 
                           text=(
                               f"<b>Имя</b>: {employee_data[1]}\n"
                               f"<b>Фамилия</b>: {employee_data[2]}\n" 
                               f"<b>Дата рождения</b>: {employee_data[3]}\n"
                               f"<b>Город</b>: {employee_data[4]}\n"
                               f"<b>Часовой пояс</b>: {employee_data[5]}\n"
                               f"<b>Должность</b>: {employee_data[6]}\n"
                               f"{hours}"
                               f"<b>Роли</b>:{employee_data[8]}\n"
                               f"<b>Кол-во лет опыта</b>: {employee_data[9]}\n"
                               f"<b>Резюме</b>: {employee_data[10]}\n"
                               f"<b>Видеовизитка</b>: {employee_data[11]}\n"
                            ),
                           parse_mode="HTML",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                [InlineKeyboardButton(text="связаться", callback_data=MyCallback_after(path="contact", 
                                          employer_tg_id=callback_data.user_tg_id, 
                                          employee_tg_id=call.from_user.id, 
                                          username=call.from_user.username, 
                                          state=(await state.get_state()).split(":")[0]
                                        ).pack()
                                )],
                                [InlineKeyboardButton(text="отклонить", callback_data=MyCallback_after(path="reject", 
                                          employer_tg_id=callback_data.user_tg_id, 
                                          employee_tg_id=call.from_user.id, 
                                          username=call.from_user.username, 
                                          state=(await state.get_state()).split(":")[0]
                                        ).pack()
                                )]
                            ]) 
    ) 
    await call.message.edit_reply_markup(reply_markup=after_respond_kb_1)
    await call.answer()
