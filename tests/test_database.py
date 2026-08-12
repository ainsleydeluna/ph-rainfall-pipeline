def test_connects_to_test_database(test_db_connection):
    with test_db_connection.cursor() as cursor:
        cursor.execute("SELECT current_database();")
        result = cursor.fetchone()

    assert result[0] == "ph_rainfall_test"

def test_city_fixture_inserts_city(
        test_db_connection,
        test_city,
):
    with test_db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT city_id FROM cities WHERE city_id = %s;",
            (test_city,),
        )
        result = cursor.fetchone()

    assert result[0] == "test_manila"


