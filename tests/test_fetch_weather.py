from src.fetch_weather import build_envelope, build_params, write_json_atomic,validate_unique_city_ids,validate_coordinate_ranges,build_weather_path,load_cities
from datetime import datetime, timezone
import json
from pathlib import Path
import pytest



def test_build_params():
    city = {"lat": 14.60420, "lon": 120.98220}

    params = build_params(city)

    assert params["latitude"] == 14.60420
    assert params["longitude"] == 120.98220
    assert params["forecast_days"] == 7
    assert params["precipitation_unit"] == "mm"


def test_build_envelope_preserves_payload():
    city = {
        "city_id": "manila",
        "city": "Manila",
        "lat": 14.60420,
        "lon": 120.98220,
        "island_group": "Luzon",
        "climate_type": "Type I",
    }
    payload = {"daily": {"time": ["2026-08-03"]}}

    envelope = build_envelope(city,payload)

    assert envelope["metadata"]["city_id"] == "manila"
    assert envelope["payload"] == payload

def test_envelope_timestamp_is_utc():
    city = {
        "city_id": "manila", "city": "Manila",
        "lat": 14.60420, "lon": 120.98220,
        "island_group": "Luzon", "climate_type": "Type I",
    }

    envelope = build_envelope(city,{})
    timestamp = datetime.fromisoformat(
        envelope["metadata"]["fetched_at_utc"]
    )

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == 0

def test_something(tmp_path):
    final_path = tmp_path / "manila.json"
    data = {"city_id": "manila", "rainfall": 12.5}

    write_json_atomic(final_path,data)

    temp_path = tmp_path / "manila.json.tmp"

    assert final_path.exists()
    assert not temp_path.exists()

    saved_data = json.loads(final_path.read_text(encoding="utf-8"))
    assert saved_data == data

def test_atomic_write_failure_keeps_existing_file(tmp_path,monkeypatch):
    final_path = tmp_path / "manila.json"
    final_path.write_text('{"old": true}', encoding="utf-8")

    def fail_replace(self,target):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(Path, "replace", fail_replace)

    with pytest.raises(OSError):
        write_json_atomic(final_path, {"new": True})

    saved_data = json.loads(final_path.read_text(encoding="utf-8"))
    assert saved_data == {"old": True}
    assert not (tmp_path / "manila.json.tmp").exists()

def test_duplicate_city_id_is_rejected():
    cities = [
        {"city_id": "manila"},
        {"city_id": "manila"},
    ]

    with pytest.raises(ValueError):
        validate_unique_city_ids(cities)

def test_invalid_latitude_is_rejected():
    cities = [
        {
            "city_id": "invalid_city",
            "lat": 95.0,
            "lon": 120.0,
        }
    ]

    with pytest.raises(ValueError):
        validate_coordinate_ranges(cities)

def test_invalid_longitude_is_rejected():
    cities = [
        {
            "city_id": "invalid_city",
            "lat": 14.0,
            "lon": 190.0,
        }
    ]

    with pytest.raises(ValueError):
        validate_coordinate_ranges(cities)      

@pytest.mark.parametrize(
        "city_id, expected_filename",
        [
            ("manila", "manila.json"),
            ("cebu", "cebu.json"),
            ("davao", "davao.json")
        ],
)

def test_build_weather_path(city_id,expected_filename):
    result = build_weather_path(
        city_id,
        "2026-08-03"
    )

    assert result.name == expected_filename
    assert result.parent.name == "dt=2026-08-03"

def test_real_payload_is_preserved():
    fixture_path = Path(
        "tests/fixtures/open_meteo_manila.json"
    )

    payload_text = fixture_path.read_text(encoding="utf-8")
    payload = json.loads(payload_text)

    city = {
        "city_id": "manila", "city": "Manila",
        "lat": 14.60420, "lon": 120.98220,
        "island_group": "Luzon", "climate_type": "Type I",
    }

    envelope = build_envelope(city,payload)

    assert envelope["payload"] == payload

def test_load_cities_reads_valid_csv(tmp_path):
    csv_path = tmp_path / "cities.csv"
    csv_path.write_text(
        "city_id,city,lat,lon,island_group,climate_type\n"
        "manila,Manila,14.60420,120.98220,Luzon,Type I\n",
        encoding="utf-8",
    )

    cities = load_cities(csv_path)

    assert len(cities) == 1
    assert cities[0]["city_id"] == "manila"
    assert cities[0]["lat"] == "14.60420"