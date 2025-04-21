from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from all_kb import get_data_kb, main_kb
from state_list import profile
from create_bot import db, logger
from aiogram.types import CallbackQuery

router = Router()

# Define callback data classes
class ConfirmDeleteCallback:
    def __init__(self, action, profile_type):
        self.action = action
        self.profile_type = profile_type
        
    def pack(self):
        return f"confirm_delete:{self.action}:{self.profile_type}"
        
    @classmethod
    def unpack(cls, callback_data):
        _, action, profile_type = callback_data.split(":")
        return cls(action, profile_type)


@router.message(Command("delete_profile"))
@router.message(F.text == "удалить профиль")
async def delete_profile_handler(message: Message, state:FSMContext):
    logger.info(f"User {message.from_user.id} initiated profile deletion.")
    await state.set_state(profile.delete_profile)
    await message.answer("Какой из профилей вы хотите удалить?", reply_markup=get_data_kb)
    
@router.message(Command("для соискателя"))
@router.message(F.text == "для соискателя", profile.delete_profile)
async def delete_employee_handler(message: Message, state:FSMContext):
    logger.info(f"User {message.from_user.id} selected to delete employee profile.")
    employee_profile = db.get_tg_id_employee(message.from_user.id)
    
    if employee_profile is not None:
        # Ask for confirmation
        confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить", 
                    callback_data=ConfirmDeleteCallback("confirm", "employee").pack()
                ),
                InlineKeyboardButton(
                    text="Нет, отменить", 
                    callback_data=ConfirmDeleteCallback("cancel", "employee").pack()
                )
            ]
        ])
        
        await message.answer(
            "Вы уверены, что хотите удалить профиль соискателя? Это действие нельзя отменить.",
            reply_markup=confirmation_keyboard
        )
    else:
        logger.warning(f"User {message.from_user.id} attempted to delete non-existent employee profile.")
        await message.answer("У вас нет анкеты соискателя.", reply_markup=main_kb)
        await state.clear()

@router.message(Command("для работодателя"))
@router.message(F.text == "для работодателя", profile.delete_profile)
async def delete_employer_handler(message: Message, state:FSMContext):
    logger.info(f"User {message.from_user.id} selected to delete employer profile.")
    employer_profile = db.get_tg_id_employer(message.from_user.id)
    
    # Debug logging to check what's being returned
    logger.info(f"Employer profile check result: {employer_profile}")
    
    if employer_profile is not None:
        # Ask for confirmation
        confirmation_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить", 
                    callback_data=ConfirmDeleteCallback("confirm", "employer").pack()
                ),
                InlineKeyboardButton(
                    text="Нет, отменить", 
                    callback_data=ConfirmDeleteCallback("cancel", "employer").pack()
                )
            ]
        ])
        
        await message.answer(
            "Вы уверены, что хотите удалить профиль работодателя? Это действие нельзя отменить.",
            reply_markup=confirmation_keyboard
        )
    else:
        logger.warning(f"User {message.from_user.id} attempted to delete non-existent employer profile.")
        await message.answer("У вас нет анкеты работодателя.", reply_markup=main_kb)
        await state.clear()


@router.callback_query(lambda c: c.data.startswith("confirm_delete:"))
async def process_delete_confirmation(call: CallbackQuery, state: FSMContext):
    callback_data = ConfirmDeleteCallback.unpack(call.data)
    
    if callback_data.action == "confirm":
        if callback_data.profile_type == "employee":
            # Delete employee profile
            db.delete_employee(call.from_user.id)
            logger.info(f"User {call.from_user.id} confirmed employee profile deletion.")
            await call.message.edit_text("Профиль соискателя успешно удален.")
            await call.message.answer("Вы можете создать новый профиль в любое время.", reply_markup=main_kb)
        else:
            # Delete employer profile
            db.delete_employer(call.from_user.id)
            logger.info(f"User {call.from_user.id} confirmed employer profile deletion.")
            await call.message.edit_text("Профиль работодателя успешно удален.")
            await call.message.answer("Вы можете создать новый профиль в любое время.", reply_markup=main_kb)
    else:
        # User canceled deletion
        logger.info(f"User {call.from_user.id} canceled profile deletion.")
        await call.message.edit_text("Удаление профиля отменено.")
        await call.message.answer("Ваш профиль остался без изменений.", reply_markup=main_kb)
    
    await state.clear()
    await call.answer()