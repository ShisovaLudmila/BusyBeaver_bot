from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from all_kb import choose_role_kb
from create_bot import logger

router = Router()


@router.message(Command("fill_form"))
@router.message(F.text == "заполнить профиль")
async def form_selection(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} selected to fill out a form.")
    await message.answer(
        "выберет в роли кого вы хотите заполнить профиль", reply_markup=choose_role_kb
    )
