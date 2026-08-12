import os
import pytest
import psycopg
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")



@pytest.fixture(scope="session")

def test_db_name():
    db_name = os.getenv("TEST_DB_NAME", "ph_rainfall_test")

    if not db_name.endswith("_test"):
        pytest.fail("Refusing to use a non-test database")

    return db_name

@pytest.fixture

def test_db_connection(test_db_name):
    connection = psycopg.connect(
        dbname=test_db_name,
        user=os.getenv("DB_USER","postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST","localhost"),
        port=int(os.getenv("DB_PORT","5432")),
    )

    yield connection
    connection.rollback()
    connection.close()

@pytest.fixture
def test_city(test_db_connection):
    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO cities
                (city_id,city,lat,lon,island_group,climate_type)
            VALUES (%s,%s,%s,%s,%s,%s);\
            """,
            ("test_manila", "Test Manila", 14.60, 120.98, "Luzon", "Type I"),
        )
    yield "test_manila"
    test_db_connection.rollback()







