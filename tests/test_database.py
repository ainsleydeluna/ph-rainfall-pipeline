from src.load_weather import (
    finish_ingestion_run,
    insert_forecast_rows,
    start_ingestion_run,
)
import psycopg
import pytest




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

def test_insert_forecast_rows(
        test_db_connection,
        committed_test_city,
        use_test_database,
):
    rows =[(
        committed_test_city,
        "2026-08-08",
        12.5,
        "2026-08-07T10:00:00+00:00",
    )]

    inserted = insert_forecast_rows(rows)

    assert inserted == 1

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM daily_weather_forecasts
            WHERE city_id = %s;
            """,
            (committed_test_city,),
        )
        count = cursor.fetchone()[0]

    assert count == 1

def test_insert_forecast_rows_is_idempotent(
    test_db_connection,
    committed_test_city,
    use_test_database,
):
    rows = [(
        committed_test_city,
        "2026-08-08",
        12.5,
        "2026-08-07T10:00:00+00:00",
    )]

    first_insert = insert_forecast_rows(rows)
    second_insert = insert_forecast_rows(rows)

    assert first_insert == 1
    assert second_insert == 0

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM daily_weather_forecasts
            WHERE city_id = %s;
            """,
            (committed_test_city,),
        )
        count = cursor.fetchone()[0]

    assert count == 1

def test_insert_forecast_rows_rolls_back_on_error(
    test_db_connection,
    committed_test_city,
    use_test_database,
):
    rows = [
        (committed_test_city, "2026-08-08", 12.5,
         "2026-08-07T10:00:00+00:00"),
        (committed_test_city, "2026-08-09", -1.0,
         "2026-08-07T10:00:00+00:00"),
    ]

    with pytest.raises(psycopg.errors.CheckViolation):
        insert_forecast_rows(rows)

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM daily_weather_forecasts
            WHERE city_id = %s;
            """,
            (committed_test_city,),
        )
        count = cursor.fetchone()[0]

    assert count == 0

def test_start_ingestion_run(
        test_db_connection,
        clean_test_audit_runs,
        use_test_database,
):
    run_id = start_ingestion_run(clean_test_audit_runs)

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT status FROM ingestion_runs WHERE run_id=%s",
            (run_id,),
         )
        result = cursor.fetchone()
    assert result[0] == "running"

def test_finish_ingestion_run(
        test_db_connection,
        clean_test_audit_runs,
        use_test_database,
):
    run_id = start_ingestion_run(clean_test_audit_runs)

    finish_ingestion_run(
        run_id,"success",10,70,70,0
    )

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT status,processed_files, prepared_rows,
                inserted_rows, failed_files, finished_at_utc
            FROM ingestion_runs
            WHERE run_id = %s;
            """,
            (run_id,),
        )
        result = cursor.fetchone()

    assert result[0] == "success"
    assert result[1:5] == (10,70,70,0)
    assert result[5] is not None





    