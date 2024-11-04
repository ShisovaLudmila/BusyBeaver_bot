import psycopg2
from config import DB_NAME, USER, PASSWORD, HOST, PORT
import os

# conn = psycopg2.connect(
#     dbname = "TelegramBotHH",
#     user = "postgres",
#     password = "admin",
#     host = "localhost",
#     port = "5432",
#     )
# print("подключение")
# conn.close()


class DataBase:
    def __init__(self):
        # Инициализация соединения с бд
        self.connection = psycopg2.connect(
            dbname=DB_NAME,
            user=USER,
            password=PASSWORD,
            host=HOST,
            port=PORT,
        )
        # self.cursor = self.conn.cursor()

    def insert_tg_id_into_user(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) FROM "user" WHERE user_tg_id = %s""", (tg_id,)
                )
                if cursor.fetchone()[0] == 0:
                    cursor.execute(
                        """INSERT INTO "user" (user_tg_id, free_vacancies_week) 
                                  VALUES(%s, 3)""",
                        (tg_id,),
                    )

    def insert_employee(
        self,
        tg_id,
        name,
        surname,
        birthdate,
        city,
        time_zone,
        job_title,
        hours,
        role,
        year_of_exp,
        resume,
        video,
    ):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO employee (employee_tg_id, name, surname, birthdate, city, time_zone, job_title, hours, role, year_of_exp, resume, video) 
                               VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        tg_id,
                        name,
                        surname,
                        birthdate,
                        city,
                        time_zone,
                        job_title,
                        hours,
                        role,
                        year_of_exp,
                        resume,
                        video,
                    ),
                )

    def insert_employer(
        self,
        tg_id,
        company,
        city,
        time_zone,
        job_title,
        hours,
        role,
        year_of_exp,
        vacancy_description,
        salary_description,
        details,
    ):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO employer (employer_tg_id, company, city, time_zone, job_title, hours, role, year_of_exp, vacancy_description, salary_description, details) 
                               VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        tg_id,
                        company,
                        city,
                        time_zone,
                        job_title,
                        hours,
                        role,
                        year_of_exp,
                        vacancy_description,
                        salary_description,
                        details,
                    ),
                )
                cursor.execute(
                    """UPDATE "user" 
                               SET free_vacancies_week=3
                               WHERE user_tg_id=%s""",
                    (tg_id,),
                )

    def get_tg_id_employee(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT employee_tg_id from employee 
                               WHERE employee_tg_id=%s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def get_tg_id_employer(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT employer_tg_id from employer 
                               WHERE employer_tg_id=%s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def get_employee(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT * from employee
                            WHERE employee_tg_id=%s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def get_employer(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT * from employer
                            WHERE employer_tg_id=%s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def delete_employee(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """DELETE FROM employee WHERE employee_tg_id=%s""", (tg_id,)
                )

    def delete_employer(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """DELETE FROM employer WHERE employer_tg_id=%s""", (tg_id,)
                )

    def employee_match(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               WITH employee AS (
                                   SELECT job_title, role, year_of_exp, employee_tg_id
                                   FROM employee 
                                   WHERE employee_tg_id = %s
                                )
                                SELECT 
                                    employer.*, match.initiator_tg_id,
                                    SUM(
                                        CASE 
                                            WHEN employer.job_title = employee.job_title THEN 50
                                            ELSE 0
                                        END +
                                        CASE 
                                            WHEN POSITION(employee.role IN employer.role) > 0 THEN 25
                                            ELSE 0
                                        END +
                                        CASE 
                                            WHEN employer.year_of_exp <= employee.year_of_exp THEN 25
                                            ELSE 0
                                        END
                                    ) AS total_score
                                FROM employer
                                CROSS JOIN employee
								LEFT JOIN match ON employee.employee_tg_id=match.employee_tg_id AND employee.employee_tg_id = match.initiator_tg_id AND employer.employer_tg_id=match.employer_tg_id
                                WHERE employee.employee_tg_id != employer.employer_tg_id
                                GROUP BY 
                                    employer.employer_tg_id, employer.company, employer.city, employer.time_zone, employer.job_title, employer.hours, employer.role, employer.year_of_exp, employer.vacancy_description, employer.salary_description, employer.details, match.initiator_tg_id
                                ORDER BY total_score DESC;
                            """,
                    (tg_id,),
                )
                return cursor.fetchall()

    def employer_match(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               WITH employer AS (
                                   SELECT job_title, role, year_of_exp, employer_tg_id
                                   FROM employer
                                   WHERE employer_tg_id = %s
                                )
                                SELECT 
                                    employee.*, match.initiator_tg_id,
                                    SUM(
                                        CASE 
                                            WHEN employee.job_title = employer.job_title THEN 50
                                            ELSE 0
                                        END +
                                        CASE 
                                            WHEN POSITION(employee.role IN employer.role) > 0 THEN 25
                                            ELSE 0
                                        END +
                                        CASE 
                                            WHEN employer.year_of_exp <= employee.year_of_exp THEN 25
                                            ELSE 0
                                        END
                                    ) AS total_score
                                FROM employee
                                CROSS JOIN employer
                                LEFT JOIN match ON employer.employer_tg_id=match.employer_tg_id AND employer.employer_tg_id = match.initiator_tg_id AND employee.employee_tg_id=match.employee_tg_id
                                WHERE employer.employer_tg_id != employee.employee_tg_id
                                GROUP BY 
                                    employee.employee_tg_id, employee.name, employee.surname, employee.birthdate, employee.city, employee.time_zone, employee.job_title, employee.hours, employee.role, employee.year_of_exp, employee.resume, employee.video, match.initiator_tg_id
                                ORDER BY total_score DESC;
                            """,
                    (tg_id,),
                )
                return cursor.fetchall()

    def set_match(self, employee_tg_id, initiator_tg_id, employer_tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO match (employee_tg_id, initiator_tg_id, employer_tg_id)
                               VALUES (%s, %s, %s)""",
                    (employee_tg_id, initiator_tg_id, employer_tg_id),
                )

    def set_match_result_true(self, employee_tg_id, initiator_tg_id, employer_tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               UPDATE match 
                               SET match_result = true
                               WHERE employee_tg_id = %s AND initiator_tg_id = %s AND employer_tg_id = %s
                               """,
                    (employee_tg_id, initiator_tg_id, employer_tg_id),
                )

    def set_match_result_false(self, employee_tg_id, initiator_tg_id, employer_tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               UPDATE match 
                               SET match_result = false
                               WHERE employee_tg_id = %s AND initiator_tg_id = %s AND employer_tg_id = %s
                               """,
                    (employee_tg_id, initiator_tg_id, employer_tg_id),
                )

    def insert_payment(
        self,
        user_tg_id,
        payments_tg_id,
        provider_tg_id,
        date,
        currenct,
        total_amount,
        number_of_months_of_subscription,
    ):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO payments (user_tg_id, payments_tg_id, provider_payments_id, date, currency, total_amount, number_of_months_of_subscription) 
                               VALUES(%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        user_tg_id,
                        payments_tg_id,
                        provider_tg_id,
                        date,
                        currenct,
                        total_amount,
                        number_of_months_of_subscription,
                    ),
                )

    # def contains_in_payments(self, user_tg_id):
    #     with self.connection as conn:
    #         with conn.cursor() as cursor:
    #             cursor.execute("""SELECT * from payments
    #                            WHERE user_tg_id=%s""", (user_tg_id,))
    #             return cursor.fetchone()

    def update_free_vacancies(self):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               UPDATE "user"
                               SET free_vacancies_week = 3
                            """
                )

    def subtract_free_vacancies(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               UPDATE "user"
                               SET free_vacancies_week = free_vacancies_week - 1
                               WHERE user_tg_id= %s""",
                    (tg_id,),
                )

    def get_end_of_subscription(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               SELECT end_of_subscription FROM "user"
                               WHERE user_tg_id= %s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def get_free_vacancies_week(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               SELECT free_vacancies_week FROM "user"
                               WHERE user_tg_id= %s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def set_free_week_subscription(self, tg_id, message_date):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               UPDATE "user"
                               SET end_of_free_week_subscription = %s + '1 WEEk'::interval 
                               WHERE user_tg_id = %s
                            """,
                    (message_date, tg_id),
                )

    def get_end_of_free_week_subscription(self, tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                               SELECT end_of_free_week_subscription FROM "user"
                               WHERE user_tg_id= %s""",
                    (tg_id,),
                )
                return cursor.fetchone()

    def change_employee_field(self, field, value, employee_tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""UPDATE employee SET {field} = %s WHERE employee_tg_id=%s""",
                    (value, employee_tg_id),
                )

    def change_employer_field(self, field, value, employer_tg_id):
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""UPDATE employer SET {field} = %s WHERE employer_tg_id=%s""",
                    (value, employer_tg_id),
                )
