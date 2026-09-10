# docker compose -f airflow/compose.yaml up -d
# docker compose -f airflow/compose.yaml ps
# http://localhost:8080

from datetime import datetime, timedelta
from pathlib import Path
from airflow.sdk import dag,task

@dag(
    dag_id="learning_file_pipeline",
    schedule=None,
    start_date=datetime(2026,9,1),
    catchup=False
)

def learning_file_pipeline():
    @task
    def create():
        folder = Path("/opt/airflow/learning_data")
        folder.mkdir(exist_ok=True)

        file_path = folder / "message.txt"
        file_path.write_text("Airflow learning file", encoding="utf-8")

        print(f"Created: {file_path}")
    @task(
        retries=1,
        retry_delay=timedelta(seconds=10),
    )
    def validate():
        file_path = Path("/opt/airflow/learning_data/message.txt")

        if not file_path.exists():
            raise FileNotFoundError("message.txt was not created")

        content = file_path.read_text(encoding="utf-8")
        if content != "Airflow learning file":
            raise ValueError("Unexpected file content")

        print("Validation passed")

    @task
    def archive():
        source = Path("/opt/airflow/learning_data/message.txt")
        archive_dir = Path("/opt/airflow/learning_data/archive")

        archive_dir.mkdir(exist_ok=True)
        destination = archive_dir / "message.txt"

        source.replace(destination)

        print(f"Archived: {destination}")

    create_task = create()
    validate_task = validate()
    archive_task = archive()

    create_task >> validate_task >> archive_task


learning_file_pipeline()