from datetime import datetime, timedelta
from pathlib import Path
import time


from airflow.sdk import dag, task

RETRY_MARKER = Path("/tmp/week9_retry_marker.txt")

@task(
    retries=1,
    retry_delay=timedelta(seconds=10),
)

def retry_test():
    if not RETRY_MARKER.exists():
        RETRY_MARKER.write_text("first attempt failed")
        raise ValueError("Intentional Week 9 retry test")

    print("Retry succeeded.")

@task(
    execution_timeout=timedelta(seconds=5),
)
def timeout_test():
    print("Starting timeout test.")
    time.sleep(2)
    print("Timeout test completed normally.")


@dag(
    dag_id="rainfall_reliability_test",
    schedule=None,
    start_date=datetime(2026, 9, 1),
    catchup=False,
)

def rainfall_reliability_test():
    retry_test()
    timeout_test()


rainfall_reliability_test()