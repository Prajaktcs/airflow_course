from airflow.decorators import dag, task
from datetime import datetime
import time

# Define default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 0,
}

PARALLEL_TASKS=100
SLEEP_TIME=20


# Define the DAG
@dag(
    "test_parallelism",
    default_args=default_args,
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    max_active_tasks=8,
    description="Test task parallelism with TaskFlow API using dynamic task mapping",
)
def test_task_parallelism():

    @task
    def generate_numbers():
        return list(range(PARALLEL_TASKS))

    # Generate data in chunks
    @task
    def add_one(x: int):
        return x + 1

    @task
    def sum_it(values):
        time.sleep(SLEEP_TIME)
        total = sum(values)
        print(f"Total was {total}")

    numbers = generate_numbers()
    print(f"Numbers: {numbers}")
    added_values = add_one.expand(x=numbers)
    sum_it(added_values)

# Instantiate the DAG
dag = test_task_parallelism()
