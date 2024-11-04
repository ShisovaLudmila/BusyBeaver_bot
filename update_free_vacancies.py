from create_bot import db
import schedule
import time


def update_vacancies():
    schedule.every().monday.at("10:00").do(db.update_free_vacancies)
    while True:
        schedule.run_pending()
        time.sleep(1)
