import psycopg2
from config import DB_NAME, USER, PASSWORD, HOST, PORT 
import os
import logger

#[p[p]] conn = psycopg2.connect(
#     dbname = "TelegramBotHH",
#     user = "postgres",
#     password = "admin",
#     host = "localhost",
#     port = "5432",
#     )
# print("подключение")
# conn.close()


import psycopg2
from config import DB_NAME, USER, PASSWORD, HOST, PORT
import logging

logger = logging.getLogger(__name__)

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
        logger.info("Database connection established")
        
        # Initialize tables
        self._initialize_tables()
        logger.info("Database tables initialized")

    def _initialize_tables(self):
            """Create all necessary tables if they don't exist"""
            with self.connection as conn:
                with conn.cursor() as cursor:
                    # Create user table
                    logger.info("Creating 'user' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS "user" (
                            id SERIAL PRIMARY KEY,
                            user_tg_id BIGINT UNIQUE NOT NULL,
                            free_vacancies_week INTEGER DEFAULT 3,
                            end_of_subscription TIMESTAMP,
                            end_of_free_week_subscription TIMESTAMP
                        )
                    """)
                    
                    # Create employee table
                    logger.info("Creating 'employee' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS employee (
                            id SERIAL PRIMARY KEY,
                            employee_tg_id BIGINT UNIQUE NOT NULL,
                            name VARCHAR(255),
                            surname VARCHAR(255),
                            birthdate VARCHAR(255),
                            city VARCHAR(255),
                            time_zone INTEGER,
                            job_title VARCHAR(255),
                            hours VARCHAR(255),
                            role VARCHAR(255),
                            year_of_exp VARCHAR(255),
                            resume VARCHAR(255),
                            video VARCHAR(255)
                        )
                    """)
                    
                    # Create employer table
                    logger.info("Creating 'employer' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS employer (
                            id SERIAL PRIMARY KEY,
                            employer_tg_id BIGINT UNIQUE NOT NULL,
                            company VARCHAR(255),
                            city VARCHAR(255),
                            time_zone INTEGER,
                            job_title VARCHAR(255),
                            hours VARCHAR(255),
                            role VARCHAR(255),
                            year_of_exp VARCHAR(255),
                            vacancy_description TEXT,
                            salary_description VARCHAR(255),
                            details VARCHAR(255)
                        )
                    """)
                    
                    # Create match table
                    logger.info("Creating 'match' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS match (
                            id SERIAL PRIMARY KEY,
                            employee_tg_id BIGINT,
                            initiator_tg_id BIGINT,
                            employer_tg_id BIGINT,
                            match_result BOOLEAN
                        )
                    """)
                    
                    # Create promocodes table
                    logger.info("Creating 'promocodes' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS promocodes (
                            id SERIAL PRIMARY KEY,
                            code VARCHAR(50) NOT NULL UNIQUE,
                            discount_percent INTEGER NOT NULL,
                            valid_until TIMESTAMP NOT NULL,
                            created_by BIGINT NOT NULL,
                            created_at TIMESTAMP DEFAULT NOW(),
                            is_active BOOLEAN DEFAULT TRUE
                        )
                    """)
                    
                    # Create promocode usage table
                    logger.info("Creating 'promocode_usage' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS promocode_usage (
                            id SERIAL PRIMARY KEY,
                            code VARCHAR(50) NOT NULL,
                            user_id BIGINT NOT NULL,
                            used_at TIMESTAMP NOT NULL,
                            UNIQUE(code, user_id)
                        )
                    """)
                    
                    # Create subscription payments table
                    logger.info("Creating 'subscription_payments' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS subscription_payments (
                            id SERIAL PRIMARY KEY,
                            user_id BIGINT NOT NULL,
                            payment_id VARCHAR(255),
                            months INTEGER NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            payment_system VARCHAR(50) DEFAULT 'robokassa'
                        )
                    """)
                    
                    # Create payment invoice table
                    logger.info("Creating 'payment_invoice' table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS payment_invoice (
                            id SERIAL PRIMARY KEY,
                            invoice_id VARCHAR(255) NOT NULL UNIQUE,
                            user_id BIGINT NOT NULL,
                            amount NUMERIC(10, 2) NOT NULL,
                            months INTEGER NOT NULL,
                            created_at TIMESTAMP DEFAULT NOW(),
                            status VARCHAR(50) DEFAULT 'pending',
                            promo_code VARCHAR(50)
                        )
                    """)
                    
                    conn.commit()
                    logger.info("All tables created successfully")

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
# Add these methods to your DataBase class in db.py

    def create_promocode(self, code, discount_percent, valid_until, created_by):
        """Create a new promo code"""
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO promocodes (code, discount_percent, valid_until, created_by) 
                    VALUES (%s, %s, %s, %s)""",
                    (code, discount_percent, valid_until, created_by)
                )
                
    def get_promocode(self, code):
        """Get promo code details if valid"""
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT code, discount_percent, valid_until 
                    FROM promocodes 
                    WHERE code = %s AND valid_until > NOW() AND is_active = TRUE""",
                    (code,)
                )
                return cursor.fetchone()
                
    def use_promocode(self, code, user_id):
        """Mark promo code as used by a user"""
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO promocode_usage (code, user_id, used_at) 
                    VALUES (%s, %s, NOW())""",
                    (code, user_id)
                )
                
    def check_promocode_usage(self, code, user_id):
        """Check if user has already used this promo code"""
        with self.connection as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT COUNT(*) FROM promocode_usage 
                    WHERE code = %s AND user_id = %s""",
                    (code, user_id)
                )
                return cursor.fetchone()[0] > 0
                
    def set_subscription(self, user_id, months, payment_id=None):
        """Set or extend user subscription"""
        with self.connection as conn:
            with conn.cursor() as cursor:
                # Check if user already has a subscription
                cursor.execute(
                    """SELECT end_of_subscription FROM "user" 
                    WHERE user_tg_id = %s""",
                    (user_id,)
                )
                current_end = cursor.fetchone()[0]
                
                if current_end and current_end > conn.cursor().execute("SELECT NOW()").fetchone()[0]:
                    # Extend existing subscription
                    cursor.execute(
                        """UPDATE "user" 
                        SET end_of_subscription = end_of_subscription + (%s || ' MONTH')::INTERVAL 
                        WHERE user_tg_id = %s""",
                        (months, user_id)
                    )
                else:
                    # Set new subscription
                    cursor.execute(
                        """UPDATE "user" 
                        SET end_of_subscription = NOW() + (%s || ' MONTH')::INTERVAL 
                        WHERE user_tg_id = %s""",
                        (months, user_id)
                    )
                    
                # Record payment if provided
                if payment_id:
                    cursor.execute(
                        """INSERT INTO subscription_payments 
                        (user_id, payment_id, months, created_at) 
                        VALUES (%s, %s, %s, NOW())""",
                        (user_id, payment_id, months)
                    )