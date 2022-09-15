import mysql.connector
import logging
from mysql.connector import errorcode
from os import environ
from time import strftime

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    datefmt=strftime("%d %b %y %H:%M:%S")
)
logger = logging.getLogger(__name__)

# other constants
DB_HOST = environ["DB_HOST"]
DB_NAME = environ["DB_NAME"]
DB_USER = environ["DB_USER"]
DB_PASSWORD = environ["DB_PASSWORD"]

USERS_TABLE = "users"
PRODUCTS_TABLE = "products"
TEMP_NAMES_TABLE = "temp_names"
TEMP_EMAILS_TABLE = "temp_emails"
TEMP_PHONES_TABLE = "temp_phones"

TABLES = {
    USERS_TABLE: (
        f"CREATE TABLE `{USERS_TABLE}` ("
        "  `user_id` int NOT NULL,"
        "  `name` varchar(32) NOT NULL,"
        "  `email` varchar(16),"
        "  `phone` varchar(16),"
        "  `bot` int(1) NOT NULL DEFAULT 0,"
        "  `paid` int(1) NOT NULL DEFAULT 0,"
        "  PRIMARY KEY (`user_id`),"
        "  UNIQUE KEY `user_id` (`user_id`)"
        ") ENGINE=InnoDB"
    ),
    TEMP_NAMES_TABLE: (
        f"CREATE TABLE `{TEMP_NAMES_TABLE}` ("
        "  `user_id` int NOT NULL,"
        "  `name` varchar(32),"
        "  PRIMARY KEY (`user_id`),"
        "  UNIQUE KEY `user_id` (`user_id`),"
        "  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    ),
    TEMP_EMAILS_TABLE: (
        f"CREATE TABLE `{TEMP_EMAILS_TABLE}` ("
        "  `user_id` int NOT NULL,"
        "  `email` varchar(32),"
        "  PRIMARY KEY (`user_id`),"
        "  UNIQUE KEY `user_id` (`user_id`),"
        "  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    ),
    TEMP_PHONES_TABLE: (
        f"CREATE TABLE `{TEMP_PHONES_TABLE}` ("
        "  `user_id` int NOT NULL,"
        "  `phone` varchar(16),"
        "  PRIMARY KEY (`user_id`),"
        "  UNIQUE KEY `user_id` (`user_id`),"
        "  FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE"
        ") ENGINE=InnoDB"
    ),
    PRODUCTS_TABLE: (
        f"CREATE TABLE `{PRODUCTS_TABLE}` ("
        "  `id` int NOT NULL AUTO_INCREMENT,"
        "  `title` varchar(32) NOT NULL,"
        "  `description` varchar(64),"
        "  `photo_url` varchar(64),"
        "  `payload` varchar(32) NOT NULL,"
        "  `price_label` varchar(32) NOT NULL,"
        "  `price` int NOT NULL,"
        "  PRIMARY KEY (`id`), UNIQUE KEY `payload` (`payload`)"
        ") ENGINE=InnoDB"
    )
}


# to create database if not exists
def create_database(cur) -> None:
    try:
        cur.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
    except mysql.connector.Error as error:
        logger.fatal(error)


# check connection, database and tables in mysql
def check_mysql() -> None:
    try:
        cnx = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except mysql.connector.Error as error:
        logger.fatal(error)
        exit("NO MYSQL CONNECTION")
    else:
        cursor = cnx.cursor()
        try:
            cursor.execute(f"USE {DB_NAME}")
        except mysql.connector.Error as error:
            if error.errno == errorcode.ER_BAD_DB_ERROR:
                create_database(cursor)
                logger.info(f"Database {DB_NAME} created successfully.")
                cnx.database = DB_NAME
            else:
                logger.fatal(error)
                exit(0)
        else:
            logger.info(f"Database {DB_NAME} already exists")
        for table_name in TABLES:
            table_description = TABLES[table_name]
            try:
                cursor.execute(table_description)
            except mysql.connector.Error as error:
                if error.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    logger.info(error)
                else:
                    logger.fatal(error)
            else:
                logger.info(f"Created table {table_name}")
        cursor.close()
        cnx.close()


# get connection to mysql database
async def get_mysql_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME
    )


async def save_main_user_data(user_id: int, name: str, bot=0) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    add_user = f"INSERT INTO {USERS_TABLE} (user_id, name, bot) " \
               f"VALUES({user_id}, '{name}', {bot})"
    try:
        cursor.execute(add_user)
    except mysql.connector.Error as error:
        logger.warning(error)
    else:
        logger.info(f"New user in database: {user_id}")
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def get_all_user_ids() -> list:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT user_id FROM {USERS_TABLE}"
    cursor.execute(query)
    records = cursor.fetchall()
    result = []
    for row in records:
        result.append(row[0])
    cursor.close()
    connection.close()
    return result


# remove user from system
async def remove_user_data(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"DELETE FROM {USERS_TABLE} WHERE user_id = '{user_id}'"
    try:
        cursor.execute(query)
    except mysql.connector.Error as error:
        logger.error(error)
    else:
        logger.info(f"Removed user from system: {user_id}")
    connection.commit()
    cursor.close()
    connection.close()


# save user column
async def save_user_column(column: str, user_id: int, value) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    add_value = f"UPDATE {USERS_TABLE} SET {column} = '{value}' WHERE user_id = {user_id}"
    try:
        cursor.execute(add_value)
    except mysql.connector.Error as error:
        logger.error(error)
    else:
        logger.info(f"Saved user value: {user_id} -> {column} -> {value}")
    connection.commit()  # make sure data is committed to the database
    cursor.close()
    connection.close()


async def save_user_name(user_id: int, name: str) -> None:
    await save_user_column("name", user_id, name)


async def save_user_email(user_id: int, email: str) -> None:
    await save_user_column("email", user_id, email)


async def save_user_phone(user_id: int, phone: str) -> None:
    await save_user_column("phone", user_id, phone)


async def save_user_paid(user_id: int, paid: bool) -> None:
    value = 1 if paid else 0
    await save_user_column("paid", user_id, value)


# get user column
async def get_user_column(column: str, user_id: int) -> str:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT {column} FROM {USERS_TABLE} WHERE user_id = {user_id}"
    cursor.execute(query)
    records = cursor.fetchall()
    if len(records) == 1:
        result = records[0][0]
    else:
        logger.warning(f"users count = {len(records)} for id: {user_id}")
        result = ""
    cursor.close()
    connection.close()
    return result


async def get_user_name(user_id: int) -> str:
    return await get_user_column("name", user_id)


async def get_user_email(user_id: int) -> str:
    return await get_user_column("email", user_id)


async def get_user_phone(user_id: int) -> str:
    return await get_user_column("phone", user_id)


async def is_user_paid(user_id: int) -> bool:
    return bool(await get_user_column("paid", user_id))


async def is_user_bot(user_id: int) -> bool:
    return bool(await get_user_column("bot", user_id))


async def remove_temp_name(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    del_old = f"DELETE FROM {TEMP_NAMES_TABLE} WHERE user_id = '{user_id}'"
    try:
        cursor.execute(del_old)
    except mysql.connector.Error as error:
        logger.error(error)
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def remove_temp_email(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    del_old = f"DELETE FROM {TEMP_EMAILS_TABLE} WHERE user_id = '{user_id}'"
    try:
        cursor.execute(del_old)
    except mysql.connector.Error as error:
        logger.error(error)
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def remove_temp_phone(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    del_old = f"DELETE FROM {TEMP_PHONES_TABLE} WHERE user_id = '{user_id}'"
    try:
        cursor.execute(del_old)
    except mysql.connector.Error as error:
        logger.error(error)
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def save_temp_name(user_id: int, temp_name: str) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    await remove_temp_name(user_id)
    add_new = f"INSERT INTO {TEMP_NAMES_TABLE} (user_id, name) " \
              f"VALUES({user_id}, '{temp_name}')"
    try:
        cursor.execute(add_new)
    except mysql.connector.Error as error:
        logger.error(error)
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def save_temp_email(user_id: int, temp_email: str) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    await remove_temp_email(user_id)
    add_new = f"INSERT INTO {TEMP_EMAILS_TABLE} (user_id, email) " \
              f"VALUES({user_id}, '{temp_email}')"
    try:
        cursor.execute(add_new)
    except mysql.connector.Error as error:
        logger.error(error)
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def save_temp_phone(user_id: int, temp_phone: str) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    await remove_temp_phone(user_id)
    add_new = f"INSERT INTO {TEMP_PHONES_TABLE} (user_id, phone) " \
              f"VALUES({user_id}, '{temp_phone}')"
    try:
        cursor.execute(add_new)
    except mysql.connector.Error as error:
        logger.error(error)
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def set_temp_name(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT name FROM {TEMP_NAMES_TABLE} WHERE user_id = {user_id}"
    cursor.execute(query)
    records = cursor.fetchall()
    if len(records) == 1:
        result = records[0][0]
        if len(result) != 0:
            user_name = result
            await save_user_name(user_id, user_name)
            await remove_temp_phone(user_id)
        else:
            logger.error(f"empty temp_name for user: {user_id}")
    else:
        logger.warning(f"temp_names count = {len(records)} for user: {user_id}")
    cursor.close()
    connection.close()


async def set_temp_email(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT email FROM {TEMP_EMAILS_TABLE} WHERE user_id = {user_id}"
    cursor.execute(query)
    records = cursor.fetchall()
    if len(records) == 1:
        result = records[0][0]
        if len(result) != 0:
            user_email = result
            await save_user_email(user_id, user_email)
            await remove_temp_phone(user_id)
        else:
            logger.error(f"empty temp_email for user: {user_id}")
    else:
        logger.warning(f"temp_emails count = {len(records)} for user: {user_id}")
    cursor.close()
    connection.close()


async def set_temp_phone(user_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT phone FROM {TEMP_PHONES_TABLE} WHERE user_id = {user_id}"
    cursor.execute(query)
    records = cursor.fetchall()
    if len(records) == 1:
        result = records[0][0]
        if len(result) != 0:
            user_phone = result
            await save_user_phone(user_id, user_phone)
            await remove_temp_phone(user_id)
        else:
            logger.error(f"empty temp_phone for user: {user_id}")
    else:
        logger.warning(f"temp_phones count = {len(records)} for user: {user_id}")
    cursor.close()
    connection.close()
