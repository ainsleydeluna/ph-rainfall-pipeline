from datetime import datetime
import subprocess
from airflow.sdk import dag,task

PROJECT_ROOT = "/opt/project"

@task
def fetch():
    subprocess.run(
        ["python","/opt/project/src/fetch_weather.py"],
        cwd=PROJECT_ROOT,
        check=True,
    )

@task
def process_and_load():
    subprocess.run(
        ["python", "/opt/project/src/load_weather.py"],
        cwd=PROJECT_ROOT,
        check=True,
    )

@dag(
    dag_id="rainfall_pipeline",
    schedule=None,
    start_date=datetime(2026,9,1),
    catchup=False,
)
def rainfall_pipeline():
    fetch_task = fetch()
    load_task = process_and_load()

    fetch_task >> load_task

rainfall_pipeline()