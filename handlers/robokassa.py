from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import hashlib
from datetime import datetime, timedelta

from config import ROBOKASSA_LOGIN, ROBOKASSA_PASSWORD1, ROBOKASSA_PASSWORD2
from create_bot import db, logger, bot

router = Router()

# This route will handle Robokassa payment notifications
async def robokassa_result_handler(request):
    """Handle payment result notifications from Robokassa"""
    try:
        # Get parameters from request
        data = await request.post()
        
        # Extract payment details
        out_sum = data.get('OutSum')
        inv_id = data.get('InvId')
        signature = data.get('SignatureValue')
        
        # Verify signature
        expected_signature = hashlib.md5(f"{out_sum}:{inv_id}:{ROBOKASSA_PASSWORD2}".encode()).hexdigest().upper()
        
        if signature.upper() != expected_signature:
            logger.warning(f"Invalid signature for payment {inv_id}")
            return web.Response(text="bad sign", status=400)
        
        # Find user by invoice ID
        user_data = db.get_user_by_invoice(inv_id)
        if not user_data:
            logger.warning(f"User not found for payment {inv_id}")
            return web.Response(text="user not found", status=400)
        
        user_id = user_data[0]
        months = user_data[1]
        
        # Activate subscription
        db.set_subscription(user_id, months, inv_id)
        
        # Notify user about successful payment
        subscription_end = datetime.now() + timedelta(days=30 * months)
        await bot.send_message(
            chat_id=user_id,
            text=(
                "✅ Оплата прошла успешно! Подписка активирована.\n\n"
                f"План: {months} {'месяц' if months == 1 else 'месяца' if months < 5 else 'месяцев'}\n"
                f"Действует до: {subscription_end.strftime('%d.%m.%Y')}\n\n"
                "Теперь вы можете искать сотрудников без ограничений."
            )
        )
        
        return web.Response(text="OK", status=200)
        
    except Exception as e:
        logger.error(f"Error processing Robokassa payment: {e}")
        return web.Response(text="error", status=500)

# Setup webhook routes
def setup_robokassa_routes(app):
    app.router.add_post('/robokassa/result', robokassa_result_handler)
