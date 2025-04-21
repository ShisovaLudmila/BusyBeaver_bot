import logging
import asyncio
from create_bot import bot, dp, logger
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
    subscription,  # Add the new subscription handler
)
from update_free_vacancies import update_vacancies
import threading

logging.basicConfig(level=logging.INFO)


async def main():
    dp.include_router(main_handlers.router)
    dp.include_router(employee_form.router)
    dp.include_router(employer_form.router)
    dp.include_router(get_profile.router)
    dp.include_router(delete_profile.router)
    dp.include_router(edit_profile.router)
    dp.include_router(fill_form.router)
    dp.include_router(find_job.router)
    dp.include_router(find_employee.router)
    dp.include_router(payments.router)
    dp.include_router(subscription.router)  # Add the new subscription router
    logger.info("Starting scheduler thread for updating vacancies")
    scheduler_thread = threading.Thread(target=update_vacancies)
    scheduler_thread.start()

    logger.info("Starting polling")
    await dp.start_polling(bot, skip_updates=False)


if __name__ == "__main__":
    logger.info("Running main function")
    asyncio.run(main())