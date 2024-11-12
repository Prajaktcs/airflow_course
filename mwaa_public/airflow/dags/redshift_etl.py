from airflow import DAG
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.providers.amazon.aws.operators.redshift import RedshiftSQLOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import datetime

AWS_CONN_ID = "aws_default"
POSTGRES_CONN_ID = "aurora_postgres"
REDSHIFT_CONN_ID = "redshift"
S3_BUCKET_NAME = "your-s3-bucket"
S3_KEY = "data/from_aurora.csv"
REDSHIFT_TABLE = "your_redshift_table"


def extract_data_from_aurora():
    postgres_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()
    query = "SELECT * FROM your_aurora_table"
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
    schedule_interval=None,
    catchup=False,
) as dag:
    extract_data = PythonOperator(
        task_id="extract_data_from_aurora",
        python_callable=extract_data_from_aurora,
    )

    load_to_redshift = RedshiftSQLOperator(
        task_id="load_data_into_redshift",
        sql=f"""
            COPY {REDSHIFT_TABLE}
            FROM 's3://{S3_BUCKET_NAME}/{S3_KEY}'
            IAM_ROLE 'your-redshift-iam-role-arn'
            CSV;
        """,
        redshift_conn_id=REDSHIFT_CONN_ID,
    )

    extract_data >> load_to_redshift
