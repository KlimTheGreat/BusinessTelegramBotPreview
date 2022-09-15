import logging
from mysql.connector import (
    Error,
    errorcode,
    connect
)
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

TABLES = {
    USERS_TABLE: (
        f"CREATE TABLE `{USERS_TABLE}` ("
        "  `user_id` int NOT NULL,"
        "  `name` varchar(32) NOT NULL,"
        "  `email` varchar(32),"
        "  `phone` varchar(16),"
        "  `temp_name` varchar(32),"
        "  `temp_email` varchar(32),"
        "  `temp_phone` varchar(16),"
        "  `bot` int(1) NOT NULL DEFAULT 0,"
        "  `paid` int(1) NOT NULL DEFAULT 0,"
        "  PRIMARY KEY (`user_id`),"
        "  UNIQUE KEY `user_id` (`user_id`)"
        ") ENGINE=InnoDB"
    ),
    PRODUCTS_TABLE: (
        f"CREATE TABLE `{PRODUCTS_TABLE}` ("
        "  `id` int NOT NULL AUTO_INCREMENT,"
        "  `title` varchar(32) NOT NULL,"
        "  `description` varchar(256),"
        "  `photo_url` varchar(64),"
        "  `payload` varchar(32) NOT NULL,"
        "  `price_label` varchar(32) NOT NULL,"
        "  `price` int NOT NULL,"
        "  PRIMARY KEY (`id`), UNIQUE KEY `payload` (`payload`)"
        ") ENGINE=InnoDB"
    ),
}


# to create database if not exists
def create_database(cur) -> None:
    try:
        cur.execute(f"CREATE DATABASE {DB_NAME} DEFAULT CHARACTER SET 'utf8mb4'")
    except Error as error:
        logger.fatal(error)


# check connection, database and tables in mysql
def check_mysql() -> None:
    try:
        cnx = connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except Error as error:
        logger.fatal(error)
        exit("NO MYSQL CONNECTION")
    else:
        cursor = cnx.cursor()
        try:
            cursor.execute(f"USE {DB_NAME}")
        except Error as error:
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
            except Error as error:
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
    return connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        db=DB_NAME
    )
