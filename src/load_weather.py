import json
import sys
from pathlib import Path
from getpass import getpass
import psycopg

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

def insert_forecast_rows(rows,password):
    sql = """
        INSERT INTO daily_weather_forecasts (
            city_id,forecast_date,precipitation_mm,fetched_at_utc
        )
        VALUES(%s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """

    with psycopg.connect(
        dbname="ph_rainfall", user="postgres",
        password=password,host="localhost",port=5432,
    ) as connection:
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

def main():
    raw_dir = Path("data/raw/weather")
    partition_dir = find_latest_partition(raw_dir)

    print("Selected partition:",partition_dir.name)

    json_files  = list(partition_dir.glob("*.json"))
    rows,failed_files = load_partition_rows(partition_dir)
    password = getpass("PostgreSQL password: ")

    inserted_count = insert_forecast_rows(rows,password)

    print("Processed files:", len(json_files))
    print("Prepared rows:",len(rows))
    print("Inserted rows:",inserted_count)
    print("Failed files:",len(failed_files))

    for filename,error in failed_files:
        print(f"FAILED: {filename} - {error}")

    return 1 if failed_files else 0

if __name__ == "__main__":
    sys.exit(main())