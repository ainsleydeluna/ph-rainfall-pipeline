CREATE TABLE cities (
    city_id TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    lat NUMERIC(8,5) NOT NULL,
    lon NUMERIC(8,5) NOT NULL,
    island_group TEXT NOT NULL,
    climate_type TEXT NOT NULL,
    CHECK (lat BETWEEN -90 AND 90),
    CHECK (lon BETWEEN -180 AND 180)
);

CREATE TABLE daily_weather_forecasts (
    city_id TEXT NOT NULL,
    forecast_date DATE NOT NULL,
    precipitation_mm NUMERIC(10,2) NOT NULL,
    fetched_at_utc TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (city_id,forecast_date,fetched_at_utc),
    FOREIGN KEY (city_id) REFERENCES cities(city_id),
    CHECK (precipitation_mm >= 0)
);