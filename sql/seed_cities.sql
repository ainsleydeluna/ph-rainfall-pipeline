COPY cities (
    city_id,
    city,
    lat,
    lon,
    island_group,
    climate_type
)

FROM '/docker-entrypoint-initdb.d/cities.csv'
WITH (FORMAT csv, HEADER true);