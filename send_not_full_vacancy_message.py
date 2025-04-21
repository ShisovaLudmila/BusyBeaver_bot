from aiogram.types import Message

async def send_not_fully_vacancy_message(message: Message, employee_data, index):
    hours = f"<b>Количество часов</b>: {employee_data[index][8]}\n" if employee_data[index][8] != "" else ""
    await message.answer(
        (
            f"<b>Имя</b>: {employee_data[index][2]}\n"
            f"<b>Фамилия</b>: {employee_data[index][3]}\n"
            f"<b>Дата рождения</b>: {employee_data[index][4]}\n"
            f"<b>Город</b>: {employee_data[index][5]}\n"
            f"<b>Часовой пояс</b>: {employee_data[index][6]}\n"
            f"<b>Должность</b>: {employee_data[index][7]}\n"
            f"{hours}"
            f"<b>Роли</b>: {employee_data[index][9]}\n"
            f"<b>Кол-во лет опыта</b>: {employee_data[index][10]}\n"
            f"<b>Резюме</b>: _________________________\n"
            f"<b>Видеовизитка</b>: _________________\n\n"
            f"Чтобы была доступна вся информация и была возможность отклика на вакансию, "
            f"Вы можете приобрести подписку по кнопке 'подписка'."
            ), parse_mode="HTML", reply_markup = None
    )