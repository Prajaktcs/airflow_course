import pulumi
import pulumi_aws as aws
import json

# Define your Postgres connection details
connection_details = {
    "conn_type": "postgres",
    "login": "airflow",
    "password": "airflow",
    "host": "postgres",
    "port": 5432,
    "schema": "airflow",
}

# Create an AWS Secrets Manager secret using the naming convention that Airflow expects.
secret = aws.secretsmanager.Secret(
    "myPostgresConnection",
    name="airflow/connections/my_postgres_conn",  # Airflow will lookup secret with this name
    description="Airflow connection for Postgres",
)

# Create a version for the secret containing our connection details as a JSON string.
secret_version = aws.secretsmanager.SecretVersion(
    "myPostgresConnectionVersion",
    secret_id=secret.id,
    secret_string=json.dumps(connection_details),
)
log_group = aws.cloudwatch.LogGroup(
    "airflow-log-group",
    name="/aws/airflow/my-airflow-env",  # Adjust this name as needed
    retention_in_days=1,  # Set retention as desired
)

pulumi.export("log_group_name", log_group.arn)
pulumi.export("connection_arn", secret.arn)
