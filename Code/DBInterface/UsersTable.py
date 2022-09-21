import logging
from time import strftime
from .Checker import (
    get_mysql_connection,
    USERS_TABLE
)
from mysql.connector import Error

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    datefmt=strftime("%d %b %y %H:%M:%S")
)
logger = logging.getLogger(__name__)


async def save_main_user_data(user_id: int, name: str, bot=0) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    add_user = f"INSERT INTO {USERS_TABLE} (user_id, name, bot) " \
               f"VALUES({user_id}, '{name}', {bot})"
    try:
        cursor.execute(add_user)
    except Error as error:
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
    except Error as error:
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
    except Error as error:
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


async def save_user_temp_name(user_id: int, temp_name: str) -> None:
    await save_user_column("temp_name", user_id, temp_name)


async def save_user_temp_email(user_id: int, temp_email: str) -> None:
    await save_user_column("temp_email", user_id, temp_email)


async def save_user_temp_phone(user_id: int, temp_phone: str) -> None:
    await save_user_column("temp_phone", user_id, temp_phone)


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


async def get_user_temp_name(user_id: int) -> str:
    return await get_user_column("temp_name", user_id)


async def get_user_temp_email(user_id: int) -> str:
    return await get_user_column("temp_email", user_id)


async def get_user_temp_phone(user_id: int) -> str:
    return await get_user_column("temp_phone", user_id)


async def is_user_paid(user_id: int) -> bool:
    return bool(await get_user_column("paid", user_id))


async def is_user_bot(user_id: int) -> bool:
    return bool(await get_user_column("bot", user_id))


async def set_perm_name(user_id: int) -> None:
    temp_name = await get_user_temp_name(user_id)
    if temp_name:
        await save_user_name(user_id, temp_name)
    else:
        logger.error(f"Can not set perm name: {user_id}")


async def set_perm_email(user_id: int) -> None:
    temp_email = await get_user_temp_email(user_id)
    if temp_email:
        await save_user_email(user_id, temp_email)
    else:
        logger.error(f"Can not set perm email: {user_id}")


async def set_perm_phone(user_id: int) -> None:
    temp_phone = await get_user_temp_phone(user_id)
    if temp_phone:
        await save_user_phone(user_id, temp_phone)
    else:
        logger.error(f"Can not set perm phone: {user_id}")
