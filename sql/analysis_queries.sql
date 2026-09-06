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

-- query 2

WITH latest_daily AS (
    SELECT
        city_id, forecast_date, precipitation_mm,
        ROW_NUMBER() OVER (
            PARTITION BY city_id, forecast_date
            ORDER BY fetched_at_utc DESC
        ) AS rn
    FROM daily_weather_forecasts
)
SELECT
    c.city,
    DATE_TRUNC('week', ld.forecast_date) AS week_start,
    SUM(ld.precipitation_mm) AS weekly_rainfall
FROM latest_daily AS ld
JOIN cities AS c
    ON ld.city_id = c.city_id
WHERE ld.rn = 1
GROUP BY c.city, week_start
ORDER BY week_start, c.city;

-- query 3

-- Query 3: Latest forecast row per city
-- PostgreSQL also supports DISTINCT ON, but ROW_NUMBER() is more portable.

WITH ranked AS (
    SELECT
        city_id,
        forecast_date,
        precipitation_mm,
        fetched_at_utc,
        ROW_NUMBER() OVER (
            PARTITION BY city_id
            ORDER BY fetched_at_utc DESC, forecast_date DESC
        ) AS rn
    FROM daily_weather_forecasts
)
SELECT *
FROM ranked
WHERE rn = 1;

SELECT
    MIN(forecast_date) AS min_date,
    MAX(forecast_date) AS max_date
FROM daily_weather_forecasts;

SELECT DISTINCT forecast_date
FROM daily_weather_forecasts
ORDER BY forecast_date
LIMIT 10;

-- query 4 

-- Query 4: Missing city/date combinations
WITH date_bounds AS (
    SELECT MIN(forecast_date) AS min_date,
           MAX(forecast_date) AS max_date
    FROM daily_weather_forecasts
),
date_spine AS (
    SELECT generate_series(
        min_date, max_date, INTERVAL '1 day'
    )::date AS forecast_date
    FROM date_bounds
),
actual_dates AS (
    SELECT DISTINCT city_id, forecast_date
    FROM daily_weather_forecasts
)
SELECT c.city, d.forecast_date
FROM cities AS c
CROSS JOIN date_spine AS d
LEFT JOIN actual_dates AS a
    ON a.city_id = c.city_id
   AND a.forecast_date = d.forecast_date
WHERE a.city_id IS NULL
ORDER BY d.forecast_date, c.city;

-- query 5
WITH ranked_daily AS (
    SELECT
        city_id, forecast_date, precipitation_mm,
        ROW_NUMBER() OVER (
            PARTITION BY city_id, forecast_date
            ORDER BY fetched_at_utc DESC
        ) AS rn
    FROM daily_weather_forecasts
)
SELECT
    c.city,
    r.forecast_date,
    r.precipitation_mm,
    SUM(r.precipitation_mm) OVER (
        PARTITION BY r.city_id
        ORDER BY r.forecast_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS rolling_7_day_rainfall
FROM ranked_daily AS r
JOIN cities AS c ON r.city_id = c.city_id
WHERE r.rn = 1
ORDER BY c.city, r.forecast_date;

-- query 6
WITH revisions AS (
    SELECT
        city_id, forecast_date, fetched_at_utc, precipitation_mm,
        LAG(precipitation_mm) OVER (
            PARTITION BY city_id, forecast_date
            ORDER BY fetched_at_utc
        ) AS previous_mm
    FROM daily_weather_forecasts
)
SELECT
    c.city,
    r.forecast_date,
    r.fetched_at_utc,
    r.precipitation_mm,
    r.previous_mm,
    r.precipitation_mm - r.previous_mm AS revision_mm
FROM revisions AS r
JOIN cities AS c ON r.city_id = c.city_id
ORDER BY c.city, r.forecast_date, r.fetched_at_utc;