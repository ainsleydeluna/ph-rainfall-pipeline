from getpass import getpass

import psycopg

password = getpass("PostgreSQL password: ")

with psycopg.connect(
    dbname="ph_rainfall",
    user="postgres",
    password=password,
    host="localhost",
    port=5432,
) as connection:
    result = connection.execute(\
        "SELECT current_database(), current_user;"
    ).fetchone()

print("Connected as:", result)