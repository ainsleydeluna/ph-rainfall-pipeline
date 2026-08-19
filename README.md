# ph-rainfall-pipeline

Beginner Data Engineering project that fetches 7-day rainfall forecasts
from Open-Meteo for 10 Philippine cities, saves raw JSON snapshots, and
loads them into PostgreSQL.

**Status:** Week 6 — Docker and Docker Compose.

**Current pipeline:**
Open-Meteo API → Python fetcher → partitioned raw JSON → PostgreSQL

## Docker Quick Start

Create your local environment file from the example:

```bash
cp .env.example .env
```

Update `DB_PASSWORD` in `.env`, then build and run the pipeline:

```bash
docker compose up --build
```

### Persistent Data

Raw JSON files are stored in the local `data/raw/` directory.

PostgreSQL data is stored in the Docker volume `postgres_data`.

To stop and remove the containers while keeping the database data:

```bash
docker compose down
```

Avoid `docker compose down -v` unless you intentionally want to delete the PostgreSQL volume and its stored data.
