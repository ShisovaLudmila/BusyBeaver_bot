from aiogram import F, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from all_kb import get_data_kb, main_kb
from state_list import profile
from create_bot import db, logger

router = Router()


@router.message(Command("profile"))
@router.message(F.text == "профиль")
async def get_profile_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested profile selection")
    await state.set_state(profile.get_profile)
    await message.answer("Выберите какой из профилей вы хотите получить", reply_markup=get_data_kb)

@router.message(F.text == "для соискателя", profile.get_profile)
async def get_employee_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested employee profile")
    if db.get_tg_id_employee(message.from_user.id) != None:
        user_data = db.get_employee(message.from_user.id)
        hours = f"<b>Количество часов</b>: {user_data[7]}\n" if user_data[7] != "" else ""
        
        # Format time zone with UTC prefix
        time_zone = user_data[5]
        time_zone_display = f"UTC{'+' if int(time_zone) > 0 else ''}{time_zone}"
        
        await message.answer(
            (
                f"Ваша анкета соискателя:\n"
                f"<b>Имя</b>: {user_data[1]}\n"
                f"<b>Фамилия</b>: {user_data[2]}\n" 
                f"<b>Дата рождения</b>: {user_data[3]}\n"
                f"<b>Город</b>: {user_data[4]}\n"
                f"<b>Часовой пояс</b>: {time_zone_display}\n"
                f"<b>Должность</b>: {user_data[6]}\n"
                f"{hours}"
                f"<b>Роли</b>: {user_data[8]}\n"
                f"<b>Кол-во лет опыта</b>: {user_data[9]}\n"
                f"<b>Резюме</b>: {user_data[10]}\n"
                f"<b>Видеовизитка</b>: {user_data[11]}\n"
            ),
            parse_mode="HTML", reply_markup=main_kb
        )
        await state.clear()
    else:
        logger.warning(f"User {message.from_user.id} has no employee profile")
        await message.answer("У вас нет анкеты соискателя.", reply_markup=main_kb)

@router.message(F.text == "для работодателя", profile.get_profile)
async def get_employer_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested employer profile")
    if db.get_tg_id_employer(message.from_user.id) != None:
        user_data = db.get_employer(message.from_user.id)
        hours = f"<b>Количество часов</b>: {user_data[5]}\n" if user_data[5] != "" else ""
        
        # Format time zone with UTC prefix
        time_zone = user_data[3]
        time_zone_display = f"UTC{'+' if int(time_zone) > 0 else ''}{time_zone}"
        
        await message.answer(
            (
                f"Ваша вакансия работодателя:\n"
                f"<b>Компания</b>: {user_data[1]}\n"
                f"<b>Город</b>: {user_data[2]}\n" 
                f"<b>Часовой пояс</b>: {time_zone_display}\n"
                f"<b>Должность</b>: {user_data[4]}\n"
                f"{hours}"
                f"<b>Роли</b>: {user_data[6]}\n"
                f"<b>Кол-во лет опыта</b>: {user_data[7]}\n"
                f"<b>Описание вакансии</b>: {user_data[8]}\n"
                f"<b>Зарплатная вилка</b>: {user_data[9]}\n"
                f"<b>Узнать подробнее</b>: {user_data[10]}\n"
            ),
            parse_mode="HTML", reply_markup=main_kb
        )
        await state.clear()
    else:
        logger.warning(f"User {message.from_user.id} has no employer profile")
        await message.answer("У вас нет анкеты работодателя.", reply_markup=main_kb)