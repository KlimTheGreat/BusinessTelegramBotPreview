import logging
from time import strftime
from Checker import (
    get_mysql_connection,
    PRODUCTS_TABLE
)
from mysql.connector import Error

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    level=logging.INFO,
    datefmt=strftime("%d %b %y %H:%M:%S")
)
logger = logging.getLogger(__name__)


async def save_main_product_data(product_id: int, name: str, bot=0) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    add_product = f"INSERT INTO {PRODUCTS_TABLE} (product_id, name, bot) " \
                  f"VALUES({product_id}, '{name}', {bot})"
    try:
        cursor.execute(add_product)
    except Error as error:
        logger.warning(error)
    else:
        logger.info(f"New product in database: {product_id}")
    connection.commit()  # Make sure data is committed to the database
    cursor.close()
    connection.close()


async def get_all_product_ids() -> list:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT product_id FROM {PRODUCTS_TABLE}"
    cursor.execute(query)
    records = cursor.fetchall()
    result = []
    for row in records:
        result.append(row[0])
    cursor.close()
    connection.close()
    return result


# remove product from system
async def remove_product_data(product_id: int) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"DELETE FROM {PRODUCTS_TABLE} WHERE product_id = '{product_id}'"
    try:
        cursor.execute(query)
    except Error as error:
        logger.error(error)
    else:
        logger.info(f"Removed product from system: {product_id}")
    connection.commit()
    cursor.close()
    connection.close()


# save product column
async def save_product_column(column: str, product_id: int, value) -> None:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    add_value = f"UPDATE {PRODUCTS_TABLE} SET {column} = '{value}' WHERE product_id = {product_id}"
    try:
        cursor.execute(add_value)
    except Error as error:
        logger.error(error)
    else:
        logger.info(f"Saved product value: {product_id} -> {column} -> {value}")
    connection.commit()  # make sure data is committed to the database
    cursor.close()
    connection.close()


async def save_product_name(product_id: int, name: str) -> None:
    await save_product_column("name", product_id, name)


# get product column
async def get_product_column(column: str, product_id: int) -> str:
    connection = await get_mysql_connection()
    cursor = connection.cursor()
    query = f"SELECT {column} FROM {PRODUCTS_TABLE} WHERE product_id = {product_id}"
    cursor.execute(query)
    records = cursor.fetchall()
    if len(records) == 1:
        result = records[0][0]
    else:
        logger.warning(f"products count = {len(records)} for id: {product_id}")
        result = ""
    cursor.close()
    connection.close()
    return result


async def get_product_name(product_id: int) -> str:
    return await get_product_column("name", product_id)
