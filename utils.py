from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from all_kb import after_respond_kb_2, after_respond_kb_1, MyCallback
from create_bot import db
import schedule
import time

async def send_vacancy_message(message: Message, data, index, state):
    if state.split(":")[0]=="find_employee":
        hours = f"<b>Количество часов</b>: {data[index][7]}\n" if data[index][7] != "" else ""
        await message.answer(
            (
                f"<b>Имя</b>: {data[index][1]}\n"
                f"<b>Фамилия</b>: {data[index][2]}\n"
                f"<b>Дата рождения</b>: {data[index][3]}\n"
                f"<b>Город</b>: {data[index][4]}\n"
                f"<b>Часовой пояс</b>: {data[index][5]}\n"
                f"<b>Должность</b>: {data[index][6]}\n"
                f"{hours}"
                f"<b>Роли</b>: {data[index][8]}\n"
                f"<b>Кол-во лет опыта</b>: {data[index][9]}\n"
                f"<b>Резюме</b>: {data[index][10]}\n"
                f"<b>Видеовизитка</b>: {data[index][11]}\n"
            ),
            parse_mode="HTML", reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Нанять", callback_data=MyCallback(path="respond", user_tg_id=data[index][0]).pack())]
                ]) if data[index][12] is None else after_respond_kb_2
        )
    else:
        hours = f"<b>Количество часов</b>: {data[index][5]}\n" if data[index][5] != "" else ""
        await message.answer(
            (
                f"<b>Компания</b>: {data[index][1]}\n"
                f"<b>Город</b>: {data[index][2]}\n"
                f"<b>Часовой пояс</b>: {data[index][3]}\n"
                f"<b>Должность</b>: {data[index][4]}\n"
                f"{hours}"
                f"<b>Роли</b>: {data[index][6]}\n"
                f"<b>Кол-во лет опыта</b>: {data[index][7]}\n"
                f"<b>Описание вакансии</b>: {data[index][8]}\n"
                f"<b>Зарплатная вилка</b>: {data[index][9]}\n"
                f"<b>Узнать подробнее</b>: {data[index][10]}\n"
            ),
            parse_mode="HTML", reply_markup= InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Откликнуться", callback_data=MyCallback(path="respond", user_tg_id=data[index][0]).pack())]
                ]) if data[index][11] is None else after_respond_kb_1
        )

async def send_not_fully_vacancy_message(message: Message, employee_data, index):
    hours = f"<b>Количество часов</b>: {employee_data[index][7]}\n" if employee_data[index][7] != "" else ""
    await message.answer(
        (
            f"<b>Имя</b>: {employee_data[index][1]}\n"
            f"<b>Фамилия</b>: {employee_data[index][2]}\n"
            f"<b>Дата рождения</b>: {employee_data[index][3]}\n"
            f"<b>Город</b>: {employee_data[index][4]}\n"
            f"<b>Часовой пояс</b>: {employee_data[index][5]}\n"
            f"<b>Должность</b>: {employee_data[index][6]}\n"
            f"{hours}"
            f"<b>Роли</b>: {employee_data[index][8]}\n"
            f"<b>Кол-во лет опыта</b>: {employee_data[index][9]}\n"
            f"<b>Резюме</b>: _________________________\n"
            f"<b>Видеовизитка</b>: _________________\n\n"
            "Чтобы была доступна вся информация и была возможность отлика на вакансию,"
            "вы можете приоберсти подписку /pay."
            ), parse_mode="HTML", reply_markup = None
    )

async def check_subscription(user_id):
    """Check if user has an active subscription or free vacancies left"""
    # Check for free trial
    free_trial = db.get_end_of_free_week_subscription(user_id)
    if free_trial and free_trial[0] is not None:
        return True
        
    # Check for paid subscription
    paid_subscription = db.get_end_of_subscription(user_id)
    if paid_subscription and paid_subscription[0] is not None:
        return True
        
    # Check for free vacancies
    free_vacancies = db.get_free_vacancies_week(user_id)
    if free_vacancies and free_vacancies[0] >= 1:
        return True
        
    return False


def update_vacancies():
    schedule.every().monday.at("10:00").do(db.update_free_vacancies)
    while True:
        schedule.run_pending()
        time.sleep(1)