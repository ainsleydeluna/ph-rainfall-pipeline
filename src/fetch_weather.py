import csv
import requests
import json
import time
from pathlib import Path
from datetime import datetime,timezone
REQUIRED_COLUMNS = [
    "city_id",
    "city",
    "lat",
    "lon",
    "island_group",
    "climate_type"
]

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_params(city):
    return {
        "latitude": city["lat"],
        "longitude": city["lon"],
        "daily": "precipitation_sum",
        "timezone": "Asia/Manila",
        "forecast_days": 7,
        "precipitation_unit": "mm",
    }

def fetch_weather(city,max_attempts=3):
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(
                FORECAST_URL,
                params=build_params(city),
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
            if attempt == max_attempts:
                raise
            print(f"RETRY: {city['city_id']} after attempt {attempt}: {error}")
            time.sleep(2)


def build_envelope(city,payload):
    return{
        "metadata": {
            "city_id": city["city_id"],
            "city": city["city"],
            "island_group": city["island_group"],
            "climate_type": city["climate_type"],
            "requested_lat": city["lat"],
            "requested_lon": city["lon"],
            "fetched_at_utc": utc_now(),
            "request_params": build_params(city),
        },
        "payload": payload,
    }

def write_json_atomic(final_path,data):
    final_path.parent.mkdir(parents="True",exist_ok=True)
    temp_path = final_path.with_suffix(final_path.suffix + ".tmp")

    with temp_path.open("w", encoding ="utf-8") as file:
        json.dump(data,file,indent=2,ensure_ascii=False)

    temp_path.replace(final_path)

def save_city_weather(city):
    payload = fetch_weather(city)
    envelope = build_envelope(city,payload)
    partition_date = envelope["metadata"]["fetched_at_utc"][:10]

    final_path = (
        Path("data/raw/weather")
        / f"dt={partition_date}"
        / f"{city["city_id"]}.json"
    )

    write_json_atomic(final_path,envelope)
    return final_path


def load_cities(csv_path):
    with csv_path.open("r",encoding="utf-8",newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != REQUIRED_COLUMNS:
            raise ValueError(
            f"Invalid CSV columns: {reader.fieldnames}"
            )
        return list(reader)

def validate_required_values(cities):
    for row_number,city in enumerate(cities, start = 2):
        if None in city:
            raise ValueError(f"Extra value in CSV row {row_number}")
        for column in REQUIRED_COLUMNS:
            value = city.get(column)
            if value is None or not value.strip():
                raise ValueError(
                    f"Missing value in row {row_number}, column {column}"
                )

def convert_coordinates(cities):
    for city in cities:
        try:
            city["lat"] = float(city["lat"])
            city["lon"] = float(city["lon"])
        except ValueError as error:
            raise ValueError(
                f"Invalid coordinates for {city["city_id"]}"
            ) from error

def validate_unique_city_ids(cities):
    seen_ids = set()

    for city in cities:
        city_id = city["city_id"]

        if city_id in seen_ids:
            raise ValueError(f"Duplicate city id: {city_id}")

        seen_ids.add(city_id)

def validate_coordinate_ranges(cities):
    for city in cities:
        lat = city["lat"]
        lon = city["lon"]

        if not -90 <= lat <= 90:
            raise ValueError(
                f"Invalid latitude for {city["city_id"]: {lat}}"
            )

        if not -180 <= lon <= 180:
            raise ValueError(
                f"Invalid longtitude for {city["city_id"]: {lon}}"
            )

def main():



    seed_path = Path("data/seeds/cities.csv")
    cities = load_cities(seed_path)
    validate_required_values(cities)
    convert_coordinates(cities)
    validate_unique_city_ids(cities)
    validate_coordinate_ranges(cities)

    EXPECTED_CITY_COUNT = 10

    if len(cities) != EXPECTED_CITY_COUNT:
        raise ValueError(
            f"Expected {EXPECTED_CITY_COUNT} cities, found {len(cities)}"
        )

    success_count = 0
    failure_count = 0

    for city in cities:
        try:
            final_path = save_city_weather(city)
            success_count += 1
            print(f"SUCCESS: {city["city_id"]} -> {final_path}")
        except Exception as error:
            failure_count += 1
            print(f"FAILED: {city['city_id']} -> {error}")

    print(f"Summary: {success_count} succeeded, {failure_count} failed")

    if failure_count > 0:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
