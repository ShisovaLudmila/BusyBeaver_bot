import sys
import logging
import traceback

# Set up logging to console with detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("debug_bot")

logger.info("Script started")

try:
    logger.info("Importing config")
    from config import BOT_TOKEN
    logger.info(f"Bot token loaded: {BOT_TOKEN[:5]}...")
    
    logger.info("Importing aiogram")
    from aiogram import Bot, Dispatcher, Router
    logger.info("aiogram imported successfully")
    
    logger.info("Creating bot instance")
    bot = Bot(token=BOT_TOKEN)
    logger.info("Bot instance created")
    
    logger.info("Creating dispatcher")
    dp = Dispatcher()
    logger.info("Dispatcher created")
    
    logger.info("Creating router")
    router = Router()
    logger.info("Router created")
    
    logger.info("Importing database")
    from db import DataBase
    logger.info("Database module imported")
    
    logger.info("Initializing database")
    db = DataBase()
    logger.info("Database initialized")
    
    logger.info("Importing handlers")
    try:
        from handlers import (
            employee_form,
            employer_form,
            main_handlers,
            get_profile,
            delete_profile,
            find_job,
            fill_form,
            find_employee,
            payments,
            edit_profile,
        )
        logger.info("All handlers imported successfully")
    except Exception as e:
        logger.error(f"Error importing handlers: {e}")
        logger.error(traceback.format_exc())
    
    logger.info("Setting up async main function")
    import asyncio
    
    async def main():
        logger.info("In main function")
        
        logger.info("Including routers")
        dp.include_router(main_handlers.router)
        logger.info("main_handlers router included")
        
        dp.include_router(employee_form.router)
        logger.info("employee_form router included")
        
        dp.include_router(employer_form.router)
        logger.info("employer_form router included")
        
        dp.include_router(get_profile.router)
        logger.info("get_profile router included")
        
        dp.include_router(delete_profile.router)
        logger.info("delete_profile router included")
        
        dp.include_router(edit_profile.router)
        logger.info("edit_profile router included")
        
        dp.include_router(fill_form.router)
        logger.info("fill_form router included")
        
        dp.include_router(find_job.router)
        logger.info("find_job router included")
        
        dp.include_router(find_employee.router)
        logger.info("find_employee router included")
        
        dp.include_router(payments.router)
        logger.info("payments router included")
        
        logger.info("Starting polling")
        await dp.start_polling(bot, skip_updates=False)
    
    logger.info("Running main function")
    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except Exception as e:
            logger.error(f"Error in asyncio.run: {e}")
            logger.error(traceback.format_exc())
            
except Exception as e:
    logger.error(f"Unhandled exception: {e}")
    logger.error(traceback.format_exc())