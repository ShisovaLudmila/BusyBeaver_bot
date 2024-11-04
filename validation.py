import re

# Регулярные выражения
regex_patterns_employee = {
    "name": r"^\S+$",  # Имя (без пробелов)
    "surname": r"^\S+$",  # Фамилия (без пробелов)
    "birthdate": r"^(0[1-9]|[12][0-9]|3[01])\.(0[1-9]|1[0-2])\.(19|20)\d{2}$",  # Дата рождения
    "city": r"^\S+$",  # Город (без пробелов)
    "experience": r"^\d+$",  # Количество лет опыта (только цифры)
    "resume": r"^(https?:\/\/)[\w-]+\.[\w-]+([^\s@]*)$",  # Общий шаблон URL резюме
    "video": r"^(https?:\/\/)[\w-]+\.[\w-]+([^\s@]*)$",  # Общий шаблон URL видеовизитки
}


def validate_input_employee(field, value):
    pattern = regex_patterns_employee.get(field)
    if pattern:
        if re.fullmatch(pattern, value):
            # Дополнительная проверка домена
            domain_match = re.search(
                r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",
                value,
            )
            if domain_match:
                domain = domain_match.group(0)
                if field in ["resume", "video"]:
                    # Проверяем на разрешённые домены
                    if domain in ["drive.google.com", "disk.yandex.ru"]:
                        return True
                    return False
                return True  # Для других полей просто возвращаем True
    return False  # Если ничего не подошло


# regex_patterns_employee = {
#     "details": r"^(https?:\/\/)?([\w-]{1,32}\.[\w-]{1,32})[^\s@]*$",  # Имя (без пробелов)
# }


# def validate_input_employer(field, value):
#     pattern = regex_patterns_employee.get(field)
#     if pattern:
#         return re.fullmatch(pattern, value) is not None
#     return False
