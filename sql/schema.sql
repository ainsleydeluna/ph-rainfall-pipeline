-- docker compose up -d db
-- docker compose exec db psql -U postgres -d ph_rainfall

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

CREATE TABLE ingestion_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    partition_date DATE NOT NULL,
    started_at_utc TIMESTAMPTZ NOT NULL,
    finished_at_utc TIMESTAMPTZ,
    status TEXT NOT NULL,
    processed_files INTEGER NOT NULL DEFAULT 0,
    prepared_rows INTEGER NOT NULL DEFAULT 0,
    inserted_rows INTEGER NOT NULL DEFAULT 0,
    failed_Files INTEGER NOT NULL DEFAULT 0,
    CHECK(status IN('running','success','failed'))
);

CREATE INDEX idx_forecasts_forecast_date
ON daily_weather_forecasts(forecast_date);

SELECT
    city_id,
    forecast_date,
    fetched_at_utc,
    ROW_NUMBER() OVER (
        PARTITION BY city_id
        ORDER BY forecast_date DESC, fetched_at_utc DESC
    ) AS rn
FROM daily_weather_forecasts;

WITH ranked_forecasts AS (
    SELECT
        city_id,
        forecast_date,
        fetched_at_utc,
        ROW_NUMBER() OVER(
            PARTITION BY city_id
            ORDER BY forecast_date DESC, fetched_at_utc DESC
        ) AS rn
    FROM daily_weather_forecasts
)


SELECT *
FROM ranked_forecasts;

WITH latest_per_day AS (
    SELECT
        city_id,
        forecast_date,
        precipitation_mm,
        ROW_NUMBER() OVER (
            PARTITION BY city_id, forecast_date
            ORDER BY fetched_at_utc DESC
        ) AS rn
    FROM daily_weather_forecasts
)


SELECT
    city_id,
    forecast_date,
    precipitation_mm,
    SUM(precipitation_mm) OVER (
        PARTITION BY city_id
        ORDER BY forecast_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7_rainfall
FROM latest_per_day
WHERE rn = 1;

SELECT *
FROM latest_per_day
WHERE rn = 1;

WITH date_spine AS (
    SELECT generate_series(
        '2026-09-01'::date,
        '2026-09-07'::date,
        INTERVAL '1 day'
    )::date AS forecast_date
)
SELECT *
FROM date_spine;

WITH date_spine AS (
    SELECT generate_series(
        '2026-09-01'::date,
        '2026-09-07'::date,
        INTERVAL '1 day'
    )::date AS forecast_date
)
SELECT c.city_id, d.forecast_date
FROM cities AS c
CROSS JOIN date_spine AS d
LEFT JOIN daily_weather_forecasts AS f
    ON f.city_id = c.city_id
    AND f.forecast_date = d.forecast_date
WHERE f.city_id IS NULL;

EXPLAIN
SELECT *
FROM daily_weather_forecasts;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM daily_weather_forecasts;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM daily_weather_forecasts
WHERE city_id = 'manila';

CREATE TABLE plan_lab (
    id BIGINT,
    city_id TEXT,
    event_date DATE,
    rainfall_mm NUMERIC
);

INSERT INTO plan_lab
SELECT
    gs AS id,
    'city_' || (gs % 100) AS city_id,
    DATE '2026-01-01' + (gs % 365) AS event_date,
    (gs % 50)::numeric AS rainfall_mm
FROM generate_series(1, 2000000) AS gs;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM plan_lab
WHERE city_id = 'city_42';

SELECT COUNT(*)
FROM plan_lab
WHERE city_id = 'city_42';

CREATE INDEX idx_plan_lab_city_id
ON plan_lab (city_id);

ANALYZE plan_lab;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM plan_lab
WHERE city_id = 'city_42';

CREATE INDEX idx_plan_lab_id
ON plan_lab (id);
ANALYZE plan_lab;

EXPLAIN (ANALYZE, BUFFERS)
SELECT *
FROM plan_lab
WHERE id = 42;

WITH latest_daily AS (
    SELECT
        city_id,
        forecast_date,
        precipitation_mm,
        ROW_NUMBER() OVER (
            PARTITION BY city_id, forecast_date
            ORDER BY fetched_at_utc DESC
        ) as rn
    FROM daily_weather_forecasts
)


SELECT 
    c.city,
    SUM(precipitation_mm) AS total_rainfall
FROM latest_daily AS ld
JOIN cities as c
    ON ld.city_id = c.city_id
WHERE ld.rn = 1
GROUP BY c.city
ORDER BY total_rainfall DESC;
