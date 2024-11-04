from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from all_kb import get_data_kb, main_kb
from state_list import profile
from create_bot import db, logger

router = Router()



@router.message(Command("delete_profile"))
@router.message(F.text == "удалить профиль")
async def delete_profile_handler(message: Message, state:FSMContext):
    logger.info(f"User {message.from_user.id} initiated profile deletion.")
    await state.set_state(profile.delete_profile)
    await message.answer("какой из профилей вы хотите удалить", reply_markup=get_data_kb)
    
@router.message(Command("для соискателя"))
@router.message(F.text == "для соискателя", profile.delete_profile)
async def delete_employee_handler(message: Message, state:FSMContext):
    logger.info(f"User {message.from_user.id} selected to delete employee profile.")
    if db.get_tg_id_employee(message.from_user.id)!=None:
        db.delete_employee(message.from_user.id)
        logger.info(f"User {message.from_user.id} employee profile deleted.")
        await message.answer("данные успешно удалены", reply_markup=main_kb)
        await state.clear()
    else:
        logger.warning(f"User {message.from_user.id} attempted to delete non-existent employee profile.")
        await message.answer("у вас нет анкеты для соискателя", reply_markup=main_kb)

@router.message(Command("для работодателя"))
@router.message(F.text == "для работодателя", profile.delete_profile)
async def delete_employer_handler(message: Message, state:FSMContext):
    logger.info(f"User {message.from_user.id} selected to delete employer profile.")
    if db.get_tg_id_employer(message.from_user.id)!=None:
        db.delete_employer(message.from_user.id)
        logger.info(f"User {message.from_user.id} employer profile deleted.")
        await message.answer("данные успешно удалены", reply_markup=main_kb)
        await state.clear()
    else:
        logger.warning(f"User {message.from_user.id} attempted to delete non-existent employer profile.")
        await message.answer("У вас нет анкеты для работадателя", reply_markup=main_kb)
