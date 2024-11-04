from config import PAYMENTS_TOKEN
from aiogram import F, Router
from aiogram import types
from aiogram.types import LabeledPrice, PreCheckoutQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from all_kb import Payments_callback
from aiogram.fsm.context import FSMContext
from state_list import payments_states
from handlers.employer_form import employer_selection
from create_bot import bot, db, logger
from datetime import timedelta

router = Router()


@router.message(Command('pay'))
@router.message(F.text == "подписка")
async def order(message: types.Message, state:FSMContext):
    logger.info(f"Received message: {message.text} from user: {message.from_user.id}")
    if db.get_tg_id_employer(message.from_user.id)!=None:
        await state.set_state(payments_states.select_subscribe)
        await message.answer("Выберите подходящую подписку:",reply_markup= InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="купить подписку на месяц", callback_data=Payments_callback(path="payment", label='1 месяц', amount=10000).pack())],
                    [InlineKeyboardButton(text="купить подписку на 3 месяца", callback_data=Payments_callback(path="payment", label='3 месяца', amount=30000).pack())],
                    [InlineKeyboardButton(text="купить подписку на 6 месяца", callback_data=Payments_callback(path="payment", label='6 месяцев', amount=60000).pack())],
                    ])
        )
    else:
        await message.answer("У вас не заполнена форма для работодателя, чтобы приобрести подписку заполните анкету:")
        await employer_selection(message, state)
        

    


        

@router.callback_query(Payments_callback.filter(F.path=="payment"), payments_states.select_subscribe)
async def order(call : types.CallbackQuery, callback_data: Payments_callback, state:FSMContext):
    logger.info(f"Callback query: {callback_data} from user: {call.from_user.id}")
    await state.set_state(payments_states.pre_confirm_query)
    await bot.send_invoice(
        chat_id=call.message.chat.id,
        title="Подписка на бота",
        description=f"Активация подписки на {callback_data.label}",
        payload=f"{callback_data.label}",
        provider_token=PAYMENTS_TOKEN,
        currency="rub",
        prices=[
            LabeledPrice(
                label=callback_data.label,
                amount=callback_data.amount
            )],
        # max_tip_amount=5000,
        # suggested_tip_amounts=[1000, 2000, 3000, 4000],
        # start_parameter=None,
        # photo_url=None,
        # photo_width=None,
        # photo_height=None,
        # need_name=True,
        # need_phone_number=True,
        # need_email=True,
        # need_shipping_address=False,
        # send_phone_number_to_provider=False,
        # send_email_to_provider=False,
        # is_flexible=False,
        # disable_notification=False,
        # protect_content=False,
        # reply_to_message_id=None,
        # allow_sending_without_reply=True,
        # reply_markup=None,
        # request_timeout=15
    )
    
@router.pre_checkout_query(payments_states.pre_confirm_query)
async def pre_checkout_query(pre_checkout_query: PreCheckoutQuery, state: FSMContext):
    logger.info(f"Pre-checkout query: {pre_checkout_query.id} from user: {pre_checkout_query.from_user.id}")
    await state.set_state(payments_states.confirm_query)
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message(F.successful_payment, payments_states.confirm_query)
async def successful_payments(message: types.Message, state: FSMContext):
    logger.info(f"Successful payment from user: {message.from_user.id}")
    await state.clear()
    payment_info = message.successful_payment
    db.insert_payment(message.from_user.id, payment_info.telegram_payment_charge_id, payment_info.provider_payment_charge_id, message.date.replace(tzinfo=None)+timedelta(hours=3), payment_info.currency, payment_info.total_amount, payment_info.invoice_payload.split(' ')[0])
    # await bot.edit_message_text(
    #     chat_id=message.chat.id,
    #     message_id=message.message_id - 1,  # Assuming the previous message is the subscription selection
    #     text=f"Оплата прошла успешно. Подписка активна до {db.get_end_of_subscription(message.from_user.id)[0]}, при приобритении подписки еще раз она продлится"
    # )
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
    await message.answer(f"Оплата прошла успешно, данные платежа\n"
                         f"ID: {message.from_user.id}\nID платежа телеграмм: {payment_info.telegram_payment_charge_id}\n"
                         f"ID платежа: {payment_info.provider_payment_charge_id}\n"
                         f"Дата платежа: {message.date.replace(tzinfo=None)+timedelta(hours=3)} (мск)\n"
                         f"Сумма платежа:{payment_info.total_amount} руб.\n\n"
                         f"Подписка активна до {db.get_end_of_subscription(message.from_user.id)[0]} (мск), при приобритении подписки еще раз она продлится.")
    
    
    # for k, v in payment_info.__dict__.items():
    #     print(f"{k} = {v}")
    # print(message.date)
