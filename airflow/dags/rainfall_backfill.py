from datetime import datetime, timedelta
import subprocess


from airflow.sdk import dag, task, get_current_context

PROJECT_ROOT = "/opt/project"



@task(
    retries=1,
    retry_delay=timedelta(seconds=10),
    execution_timeout=timedelta(minutes=2),
)
def load():
    context = get_current_context()

    partition_date = (
        context["data_interval_start"]
        .date()
        .isoformat()
    )

    subprocess.run(
        ["python", "/opt/project/src/load_weather.py",
         "--partition-date", partition_date],
         cwd=PROJECT_ROOT,
         check=True,

    )

@dag(
    dag_id="rainfall_backfill",
    schedule="@daily",
    start_date=datetime(2026, 7, 28),
    catchup=False,
)



def rainfall_backfill():
    load()

rainfall_backfill()