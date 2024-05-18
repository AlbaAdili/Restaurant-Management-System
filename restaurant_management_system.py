import pymysql
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from decimal import Decimal
import datetime

# MySQL connection details
mysql_host = 'localhost'
mysql_user = 'root'
mysql_password = ''
mysql_db = 'restaurant_management_system'

# MongoDB connection details
mongo_host = 'localhost'
mongo_port = 27017  # Default port for MongoDB
mongo_db_name = 'restaurant_management_system'

def convert_value(value):
    """
    Convert values to types that MongoDB can handle.
    """
    if isinstance(value, Decimal):
        return float(value)
    elif isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.datetime.min.time())
    elif isinstance(value, datetime.timedelta):
        return value.total_seconds()
    return value

try:
    # Connect to MySQL
    mysql_conn = pymysql.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_password,
        db=mysql_db
    )
    mysql_cursor = mysql_conn.cursor()

    # Connect to MongoDB
    mongo_client = MongoClient(mongo_host, mongo_port, serverSelectionTimeoutMS=5000)
    mongo_db = mongo_client[mongo_db_name]

    # Check MongoDB connection
    mongo_client.server_info()

    # Fetch all tables in the MySQL database
    mysql_cursor.execute("SHOW TABLES")
    tables = mysql_cursor.fetchall()

    for (table_name,) in tables:
        try:
            # Use backticks for table names to avoid SQL syntax errors with reserved keywords
            mysql_cursor.execute(f"SELECT * FROM `{table_name}`")
            rows = mysql_cursor.fetchall()

            # Fetch column names for the table
            column_query = f"SHOW COLUMNS FROM `{table_name}`"
            mysql_cursor.execute(column_query)
            columns = [column[0] for column in mysql_cursor.fetchall()]

            # Prepare data for MongoDB
            mongo_collection = mongo_db[table_name]
            mongo_data = []
            for row in rows:
                doc = {column: convert_value(value) for column, value in zip(columns, row)}
                mongo_data.append(doc)

            # Insert data into MongoDB
            if mongo_data:
                mongo_collection.insert_many(mongo_data)
                print(f"Inserted {len(mongo_data)} documents into {table_name} collection.")
        except Exception as e:
            print(f"An error occurred while processing table {table_name}: {e}")

    # Close MySQL connection
    mysql_cursor.close()
    mysql_conn.close()

    # Close MongoDB connection
    mongo_client.close()

except pymysql.MySQLError as e:
    print(f"MySQL error: {e}")
except ServerSelectionTimeoutError as e:
    print(f"MongoDB connection error: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
