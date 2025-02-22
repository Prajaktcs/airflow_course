from airflow import DAG
from datetime import datetime
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator


# Assume the SecretsManagerBackend is configured in airflow.cfg or env vars.
with DAG(
    dag_id="secrets_manager_demo",
    start_date=datetime(2023, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:
    # Use PostgresOperator to execute SQL and push results to XCom
    list_tables = PostgresOperator(
        task_id="list_tables",
        postgres_conn_id="my_postgres_conn",  # Ensure this connection is set via your secrets backend
        sql="""
            SELECT tablename
            FROM pg_catalog.pg_tables
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
        """,
        do_xcom_push=True,  # This pushes the query result to XCom
    )

    def print_tables(**context):
        # Pull the results from the previous task's XCom
        tables = context["ti"].xcom_pull(task_ids="list_tables")
        if tables:
            print("Tables in the database:")
            for row in tables:
                print(f" - {row[0]}")
        else:
            print("No tables found.")

    # Use PythonOperator to print the output of the SQL query
    print_tables_task = PythonOperator(
        task_id="print_tables",
        python_callable=print_tables,
        provide_context=True,
    )

    list_tables >> print_tables_task
