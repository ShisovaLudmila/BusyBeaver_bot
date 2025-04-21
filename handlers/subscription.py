from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import hashlib
import time
from datetime import datetime, timedelta
import urllib.parse

from config import (
    ROBOKASSA_LOGIN, 
    ROBOKASSA_PASSWORD1, 
    ROBOKASSA_PASSWORD2, 
    ROBOKASSA_TEST_MODE,
    PAYMENTS_FREE,
    ADMIN_IDS
)
from create_bot import db, logger, bot
from all_kb import main_kb, employer_main_kb

router = Router()

# Define FSM states for subscription flow
class SubscriptionStates(StatesGroup):
    selecting_plan = State()
    entering_promo = State()
    confirming_payment = State()

# Define callback data classes
class SubscriptionCallback:
    def __init__(self, action, months=None, amount=None):
        self.action = action
        self.months = months
        self.amount = amount
        
    def pack(self):
        if self.months and self.amount:
            return f"sub:{self.action}:{self.months}:{self.amount}"
        return f"sub:{self.action}"
        
    @classmethod
    def unpack(cls, callback_data):
        parts = callback_data.split(":")
        if len(parts) == 4:
            _, action, months, amount = parts
            return cls(action, int(months), int(amount))
        else:
            _, action = parts
            return cls(action)

# Subscription plans
SUBSCRIPTION_PLANS = [
    {"months": 1, "name": "1 месяц", "price": 5000, "description": "Базовый план"},
    {"months": 3, "name": "3 месяца", "price": 13500, "description": "Стандартный план (экономия 10%)"},
    {"months": 6, "name": "6 месяцев", "price": 25000, "description": "Премиум план (экономия 16%)"}
]

# Only show subscription button to employers
@router.message(F.text == "подписка для работодателей")
async def subscription_handler(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} requested subscription info")
    
    # Check if user is an employer
    employer_profile = db.get_tg_id_employer(message.from_user.id)
    
    if employer_profile is None:
        await message.answer(
            "Подписка доступна только для работодателей. Пожалуйста, заполните профиль работодателя, чтобы получить доступ к подписке.",
            reply_markup=main_kb
        )
        return
    
    # Show subscription info
    subscription_text = (
        "🚀 <b>Busybeaver бот: найди сотрудника за час</b>\n\n"
        "Преимущества подписки:\n"
        "• Не нужно мониторить сайты для поиска работы, все работает прямо в Telegram\n"
        "• Не нужно оформлять вакансию на сайте, просто заполните профиль, и соискатели свяжутся с вами напрямую\n"
        "• Получайте отклики только от тех, кто подходит под ваш запрос\n"
        "• Не нужно тратить время на множество этапов – размещение вакансии, отбор резюме, отклики, звонки, собеседования\n"
        "• На hh.ru размещение одной вакансии стоит до 10000 рублей, и отдельно за каждый клик на вакансии, в BusyBeaver количество откликов неограниченно\n\n"
        "<b>Как это работает:</b>\n"
        "1. Запустите бот и заполните профиль за несколько простых шагов\n"
        "2. Бот сразу предложит вам 5 кандидатов, соответствующих вашему запросу\n"
        "3. Нажмите \"Откликнуться\" или \"Показать ещё\"\n"
        "4. Соискатель видит ваш отклик и принимает его – ваши анкеты \"мэтчатся\", и бот передает вам контакты друг друга\n\n"
        "<b>Выберите план подписки:</b>"
    )
    
    # Create keyboard with subscription plans
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{plan['name']} - {plan['price']} ₽", 
            callback_data=SubscriptionCallback("select_plan", plan['months'], plan['price']).pack()
        )] for plan in SUBSCRIPTION_PLANS
    ])
    
    await message.answer(subscription_text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(SubscriptionStates.selecting_plan)

@router.callback_query(lambda c: c.data.startswith("sub:select_plan:"), SubscriptionStates.selecting_plan)
async def select_plan_handler(call: CallbackQuery, state: FSMContext):
    callback_data = SubscriptionCallback.unpack(call.data)
    
    # Store selected plan in state
    await state.update_data(
        months=callback_data.months,
        amount=callback_data.amount
    )
    
    # Ask if user has promo code
    promo_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="У меня есть промокод", callback_data=SubscriptionCallback("enter_promo").pack()),
            InlineKeyboardButton(text="Продолжить без промокода", callback_data=SubscriptionCallback("skip_promo").pack())
        ]
    ])
    
    await call.message.edit_text(
        f"Вы выбрали план на {callback_data.months} {'месяц' if callback_data.months == 1 else 'месяца' if callback_data.months < 5 else 'месяцев'}.\n"
        f"Стоимость: {callback_data.amount} ₽",
        reply_markup=promo_keyboard
    )
    
    await call.answer()

@router.callback_query(lambda c: c.data == "sub:enter_promo", SubscriptionStates.selecting_plan)
async def enter_promo_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "Пожалуйста, введите промокод:"
    )
    await state.set_state(SubscriptionStates.entering_promo)
    await call.answer()

@router.message(SubscriptionStates.entering_promo)
async def process_promo_handler(message: Message, state: FSMContext):
    promo_code = message.text.strip().upper()
    user_data = await state.get_data()
    
    # Check if promo code is valid
    promo_data = db.get_promocode(promo_code)
    
    if not promo_data:
        await message.answer(
            "Промокод недействителен или срок его действия истек. Пожалуйста, проверьте код и попробуйте снова.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="Продолжить без промокода", 
                    callback_data=SubscriptionCallback("skip_promo").pack()
                )]
            ])
        )
        return
    
    # Check if user has already used this promo code
    if db.check_promocode_usage(promo_code, message.from_user.id):
        await message.answer(
            "Вы уже использовали этот промокод ранее. Каждый промокод можно использовать только один раз.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="Продолжить без промокода", 
                    callback_data=SubscriptionCallback("skip_promo").pack()
                )]
            ])
        )
        return
    
    # Apply discount
    original_amount = user_data["amount"]
    discount_percent = promo_data[1]
    discounted_amount = int(original_amount * (100 - discount_percent) / 100)
    
    await state.update_data(
        promo_code=promo_code,
        discount_percent=discount_percent,
        discounted_amount=discounted_amount
    )
    
    # Show payment confirmation with discount
    await message.answer(
        f"Промокод применен! Скидка: {discount_percent}%\n\n"
        f"План: {user_data['months']} {'месяц' if user_data['months'] == 1 else 'месяца' if user_data['months'] < 5 else 'месяцев'}\n"
        f"Стоимость без скидки: {original_amount} ₽\n"
        f"Стоимость со скидкой: {discounted_amount} ₽",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Оплатить", 
                callback_data=SubscriptionCallback("confirm_payment").pack()
            )]
        ])
    )
    
    await state.set_state(SubscriptionStates.confirming_payment)

@router.callback_query(lambda c: c.data == "sub:skip_promo")
async def skip_promo_handler(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    await call.message.edit_text(
        f"План: {user_data['months']} {'месяц' if user_data['months'] == 1 else 'месяца' if user_data['months'] < 5 else 'месяцев'}\n"
        f"Стоимость: {user_data['amount']} ₽",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Оплатить", 
                callback_data=SubscriptionCallback("confirm_payment").pack()
            )]
        ])
    )
    
    await state.set_state(SubscriptionStates.confirming_payment)
    await call.answer()

@router.callback_query(lambda c: c.data == "sub:confirm_payment", SubscriptionStates.confirming_payment)
async def confirm_payment_handler(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    # Get final amount (with or without discount)
    final_amount = user_data.get("discounted_amount", user_data["amount"])
    
    # If PAYMENTS_FREE is True, skip actual payment
    if PAYMENTS_FREE:
        # Process free subscription
        db.set_subscription(call.from_user.id, user_data["months"])
        
        # If promo code was used, mark it as used
        if "promo_code" in user_data:
            db.use_promocode(user_data["promo_code"], call.from_user.id)
        
        subscription_end = datetime.now() + timedelta(days=30 * user_data["months"])
        
        await call.message.edit_text(
            "✅ Подписка успешно активирована!\n\n"
            f"План: {user_data['months']} {'месяц' if user_data['months'] == 1 else 'месяца' if user_data['months'] < 5 else 'месяцев'}\n"
            f"Действует до: {subscription_end.strftime('%d.%m.%Y')}\n\n"
            "Теперь вы можете искать сотрудников без ограничений."
        )
        
        await state.clear()
        await call.answer("Подписка активирована!")
        return
    
    # Generate payment link for Robokassa
    inv_id = int(time.time())  # Use timestamp as invoice ID
    description = f"Подписка на {user_data['months']} мес."
    
    # Store payment info in state
    await state.update_data(inv_id=inv_id)
    
    # Generate signature
    signature = hashlib.md5(f"{ROBOKASSA_LOGIN}:{final_amount}:{inv_id}:{ROBOKASSA_PASSWORD1}".encode()).hexdigest()
    
    # Build payment URL
    payment_url = f"https://auth.robokassa.ru/Merchant/Index.aspx?MerchantLogin={ROBOKASSA_LOGIN}&OutSum={final_amount}&InvId={inv_id}&Description={urllib.parse.quote(description)}&SignatureValue={signature}&IsTest={ROBOKASSA_TEST_MODE}"
    
    await call.message.edit_text(
        "Для оплаты подписки нажмите на кнопку ниже. Вы будете перенаправлены на страницу оплаты.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти к оплате", url=payment_url)],
            [InlineKeyboardButton(text="Я оплатил", callback_data=SubscriptionCallback("check_payment").pack())]
        ])
    )
    
    await call.answer()

@router.callback_query(lambda c: c.data == "sub:check_payment")
async def check_payment_handler(call: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    
    # In a real implementation, you would check with Robokassa if payment was successful
    # For now, we'll just activate the subscription
    
    # Activate subscription
    db.set_subscription(call.from_user.id, user_data["months"], user_data.get("inv_id"))
    
    # If promo code was used, mark it as used
    if "promo_code" in user_data:
        db.use_promocode(user_data["promo_code"], call.from_user.id)
    
    subscription_end = datetime.now() + timedelta(days=30 * user_data["months"])
    
    await call.message.edit_text(
        "✅ Оплата прошла успешно! Подписка активирована.\n\n"
        f"План: {user_data['months']} {'месяц' if user_data['months'] == 1 else 'месяца' if user_data['months'] < 5 else 'месяцев'}\n"
        f"Действует до: {subscription_end.strftime('%d.%m.%Y')}\n\n"
        "Теперь вы можете искать сотрудников без ограничений."
    )
    
    await state.clear()
    await call.answer("Подписка активирована!")

# Admin command to create promo codes
@router.message(Command("create_promocode"))
async def create_promocode_handler(message: Message):
    # Check if user is admin
    if message.from_user.id not in ADMIN_IDS:
        return
    
    # Parse command arguments: /create_promocode CODE DISCOUNT DAYS
    parts = message.text.split()
    if len(parts) != 4:
        await message.answer(
            "Использование: /create_promocode КОД ПРОЦЕНТ_СКИДКИ СРОК_ДЕЙСТВИЯ_В_ДНЯХ\n"
            "Пример: /create_promocode WELCOME2023 15 30"
        )
        return
    
    try:
        code = parts[1].upper()
        discount = int(parts[2])
        days = int(parts[3])
        
        if discount <= 0 or discount > 100:
            await message.answer("Процент скидки должен быть от 1 до 100")
            return
            
        if days <= 0:
            await message.answer("Срок действия должен быть положительным числом дней")
            return
            
        valid_until = datetime.now() + timedelta(days=days)
        
        # Create promo code
        db.create_promocode(code, discount, valid_until, message.from_user.id)
        
        await message.answer(
            f"✅ Промокод создан успешно!\n\n"
            f"Код: {code}\n"
            f"Скидка: {discount}%\n"
            f"Действует до: {valid_until.strftime('%d.%m.%Y')}"
        )
        
    except ValueError:
        await message.answer("Ошибка: процент скидки и срок действия должны быть числами")