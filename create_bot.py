from aiogram import Bot, Dispatcher, Router
from config import BOT_TOKEN
from db import DataBase
import logging
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)
db= DataBase()
router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

