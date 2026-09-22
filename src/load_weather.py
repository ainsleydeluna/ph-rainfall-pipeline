import os
import json
import sys
from pathlib import Path
import psycopg
import argparse
from datetime import date
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def connect_database():
    return psycopg.connect(
        dbname=os.getenv("DB_NAME", "ph_rainfall"),
        user=os.getenv("DB_USER","postgres"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST","localhost"),
        port=int(os.getenv("DB_PORT","5432"))
    )

def load_json(path):
    with path.open("r", encoding ="utf-8") as file:
        return json.load(file)


def extract_forecast_rows(envelope):
    metadata = envelope["metadata"]
    daily = envelope["payload"]["daily"]
    rows = []

    dates = daily["time"]
    precipitation_values = daily["precipitation_sum"]

    if len(dates) != len(precipitation_values):
        raise ValueError(
            "Forecast dates and precipitation lengths differ"
        )

    for date,precipitation in zip(
        dates,
        precipitation_values,
    ):
        rows.append((
            metadata["city_id"],
            date,
            precipitation,
            metadata["fetched_at_utc"],
        ))
    return rows


def load_partition_rows(partition_dir):
    all_rows = []
    failed_files = []

    for json_path in sorted(partition_dir.glob("*.json")):
        try:
            envelope = load_json(json_path)
            rows = extract_forecast_rows(envelope)
            all_rows.extend(rows)
        except (OSError, KeyError,ValueError, json.JSONDecodeError) as error:
            failed_files.append((json_path.name, str(error)))

    return all_rows, failed_files

def insert_forecast_rows(rows):
    sql = """
        INSERT INTO daily_weather_forecasts (
            city_id,forecast_date,precipitation_mm,fetched_at_utc
        )
        VALUES(%s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """

    with connect_database() as connection:
        with connection.cursor() as cursor:
            cursor.executemany(sql,rows)
            return cursor.rowcount


def find_latest_partition(raw_dir):
    partitions = []

    for path in raw_dir.glob("dt=*"):
        if path.is_dir():
            partitions.append(path)

    partitions = sorted(partitions)

    if not partitions:
        raise FileNotFoundError("No weather partitions found")

    return partitions[-1]

def start_ingestion_run(partition_date):
    sql = """
        INSERT INTO ingestion_runs (
            partition_date,started_at_utc,status
        )
        VALUES (%s, NOW(), 'running')
        RETURNING run_id;
    """
    with connect_database() as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql, (partition_date,))
            return cursor.fetchone()[0]

def finish_ingestion_run(
        run_id,status,processed_files,prepared_rows,inserted_rows,
        failed_files,
):
        sql = """
            UPDATE ingestion_runs
            SET finished_at_utc = NOW(),status = %s,
                processed_files = %s, prepared_rows = %s,
                inserted_rows = %s, failed_files = %s
            WHERE run_id = %s;
        """

        values = (
            status,processed_files,prepared_rows,
            inserted_rows,failed_files,run_id,
        )

        with connect_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, values)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--partition-date",
        default=None,
        help="Partition date in YYYY-MM-DD format",
    )
    return parser.parse_args()

def validate_partition_date(value):
    if value is None:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(
            "partition date must use YYYY-MM-DD"
        )

def select_partition(raw_dir, partition_date):
    if partition_date is None:
        return find_latest_partition(raw_dir)

    partition_dir = raw_dir / f"dt={partition_date.isoformat()}"

    if not partition_dir.exists():
        raise FileNotFoundError(
            f"Partition not found: {partition_dir}"
        )
    return partition_dir


def main():
    args = parse_args()
    partition_date = validate_partition_date(args.partition_date)

    raw_dir = Path("data/raw/weather")
    partition_dir = select_partition(raw_dir, partition_date)
    partition_date = partition_dir.name.removeprefix("dt=")

    run_id = start_ingestion_run(partition_date)

    processed_files = 0
    prepared_rows = 0
    inserted_rows = 0
    failed_files = []
    status = "failed"

    try:
        json_files  = list(partition_dir.glob("*.json"))
        processed_files = len(json_files)

        rows,failed_files = load_partition_rows(partition_dir)
        prepared_rows = len(rows)
        inserted_rows = insert_forecast_rows(rows)
        status = "failed" if failed_files else "success"

    finally:
        finish_ingestion_run(
            run_id,
            status,
            processed_files,
            prepared_rows,
            inserted_rows,
            len(failed_files),
        )

    print("Processed files:", len(json_files))
    print("Prepared rows:",len(rows))
    print("Inserted rows:",inserted_rows)
    print("Failed files:",len(failed_files))

    for filename,error in failed_files:
        print(f"FAILED: {filename} - {error}")

    return 1 if failed_files else 0

if __name__ == "__main__":
    sys.exit(main())