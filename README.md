# ph-rainfall-pipeline

Batch ELT pipeline ingesting Open-Meteo daily weather for 8 Philippine
cities into Postgres, orchestrated with Airflow 3, modeled with dbt
(star schema: dim_city, dim_date, fact_weather_daily), landed to a
Hive-partitioned S3 lake queried via Glue/Athena, served with Streamlit.

**Status:** Week 1 — repo foundation. 26-week build, Jul–Dec 2026.

**Planned architecture:**
Open-Meteo API → Python ingest → Postgres → dbt marts → S3 → Glue/Athena → Streamlit