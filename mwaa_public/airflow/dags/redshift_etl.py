from airflow import DAG
from airflow.models import Variable
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime
import random
import string

AWS_CONN_ID = "aws_default"
POSTGRES_CONN_ID = "aurora_postgres"
REDSHIFT_CONN_ID = "redshift"
S3_BUCKET_NAME = "my-data-exchange-bucket-937696862165"
S3_KEY = "data/from_aurora.csv"
REDSHIFT_TABLE = "aurora_table"


def random_str_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


def initialize_schema_postgres():
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    with postgres_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            query = "CREATE TABLE IF NOT EXISTS aurora_table(id serial primary key, value varchar(50))"
            cursor.execute(query)
        conn.commit()


def initialize_data_postgres():
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    with postgres_hook.get_conn() as conn:
        with conn.cursor() as cursor:
            for _ in range(1, 10):
                query = f"insert into aurora_table(value) values('{random_str_generator()}')"
                cursor.execute(query)
        conn.commit()


def extract_data_from_aurora():
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()
    query = "SELECT * FROM aurora_table"
    cursor.execute(query)

    rows = cursor.fetchall()
    # Transform data as needed, then upload to S3
    s3 = S3Hook(aws_conn_id=AWS_CONN_ID)
    csv_data = "\n".join([",".join(map(str, row)) for row in rows])
    s3.load_string(csv_data, key=S3_KEY, bucket_name=S3_BUCKET_NAME, replace=True)
    cursor.close()
    conn.close()


default_args = {"start_date": datetime(2023, 1, 1), "retries": 1}

with DAG(
    "aurora_to_redshift",
    default_args=default_args,
    schedule_interval="*/5 * * * *",
    catchup=False,
) as dag:
    postgres_schema = PythonOperator(
        task_id="initialize_postgres_schema",
        python_callable=initialize_schema_postgres,
    )

    postgres_data = PythonOperator(
        task_id="initialize_postgres_data",
        python_callable=initialize_data_postgres,
    )

    extract_data = PythonOperator(
        task_id="extract_data_from_aurora",
        python_callable=extract_data_from_aurora,
    )

    # Task to create a table in Redshift
    init_redshift_schema = PostgresOperator(
        task_id="init_redshift_schema",
        sql="/sql/redshift_aurora.sql",
        postgres_conn_id=REDSHIFT_CONN_ID,
    )

    load_to_redshift = S3ToRedshiftOperator(
        task_id="load_data_into_redshift",
        table=REDSHIFT_TABLE,
        schema="public",
        s3_bucket=S3_BUCKET_NAME,
        s3_key=S3_KEY,
        method="UPSERT",
        upsert_keys=["id"],
        redshift_conn_id=REDSHIFT_CONN_ID,
        copy_options=["CSV", "DELIMITER ','"],
    )

    postgres_schema >> postgres_data
    postgres_data >> extract_data >> init_redshift_schema >> load_to_redshift
