import json
import pytest
from src.load_weather import extract_forecast_rows, load_json,load_partition_rows, find_latest_partition



def test_load_json_reads_valid_file(tmp_path):
    json_path = tmp_path / "weather.json"
    expected = {"city_id": "manila", "rainfall": 12.5}
    json_path.write_text(json.dumps(expected), encoding="utf-8")

    result = load_json(json_path)

    assert result == expected


def test_extract_forecast_rows():
    envelope = {
        "metadata": {
            "city_id": "manila",
            "fetched_at_utc": "2026-08-07T10:00:00+00:00",
        },
        "payload": {"daily": {
            "time": ["2026-08-08", "2026-08-09"],
            "precipitation_sum": [12.5,4.0],
        }},
    }

    rows = extract_forecast_rows(envelope)
    assert len(rows) == 2
    assert rows[0] == ("manila","2026-08-08",12.5,"2026-08-07T10:00:00+00:00")

def test_extract_rows_rejects_mismatched_lengths():
    envelope = {
        "metadata": {
            "city_id": "manila",
            "fetched_at_utc": "2026-08-07T10:00:00+00:00",
        },
        "payload": {"daily": {
            "time": ["2026-08-08", "2026-08-09"],
            "precipitation_sum": [12.5],
        }},
    }

    with pytest.raises(ValueError):
        extract_forecast_rows(envelope)

def test_load_partition_rows_isolates_broken_file(tmp_path):
    partition_dir = tmp_path / "dt=2026-08-07"
    partition_dir.mkdir()

    valid_envelope = {
        "metadata": {
            "city_id": "manila",
            "fetched_at_utc": "2026-08-07T10:00:00+00:00",
        },
        "payload": {"daily": {
            "time": ["2026-08-08"],
            "precipitation_sum": [12.5],
        }},
    }

    valid_path = partition_dir / "manila.json"
    valid_path.write_text(
        json.dumps(valid_envelope),
        encoding="utf-8",
    )

    broken_path = partition_dir / "broken.json"
    broken_path.write_text("{broken json", encoding="utf-8")

    rows, failed_files = load_partition_rows(partition_dir)

    assert len(rows) == 1
    assert rows[0][0] == "manila"

    assert len(failed_files) == 1
    assert failed_files[0][0] == "broken.json"

def test_find_latest_partition(tmp_path):
    (tmp_path / "dt=2026-08-01").mkdir()
    (tmp_path / "dt=2026-08-07").mkdir()
    (tmp_path / "dt=2026-08-03").mkdir()

    latest = find_latest_partition(tmp_path)

    assert latest.name == "dt=2026-08-07"

def test_find_latest_partition_ignores_files(tmp_path):
    (tmp_path / "dt=2026-08-03").mkdir()
    (tmp_path / "dt=2026-08-09").write_text(
        "not a directory",
        encoding="utf-8",
    )

    latest = find_latest_partition(tmp_path)

    assert latest.name == "dt=2026-08-03"

def test_find_latest_partition_raises_when_none_exist(tmp_path):
    with pytest.raises(FileNotFoundError):
        find_latest_partition(tmp_path)