import os
import json

import pulumi
import pulumi_aws as aws

from iam import mwaa_execution_role
from network import private_subnet_1, private_subnet_2, security_group
from dashboard import dashboard


current = aws.get_caller_identity()

encryption_key = aws.kms.Key(
    "encryption_key",
    description="Key for mwaa",
)

key_policy = aws.kms.KeyPolicy(
    "example",
    key_id=encryption_key.id,
    policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Id": "key-default-1",
            "Statement": [
                {
                    "Sid": "Enable IAM User Permissions",
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"arn:aws:iam::{current.account_id}:root",
                    },
                    "Action": "kms:*",
                    "Resource": "*",
                }
            ],
        }
    ),
)

bucket = aws.s3.BucketV2(
    f"mwaa-bucket-{current.account_id}",
    bucket=f"mwaa-bucket-{current.account_id}",
    force_destroy=True,
)

sse_config = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "encryption",
    bucket=bucket.id,
    rules=[
        {
            "apply_server_side_encryption_by_default": {
                "kms_master_key_id": encryption_key.arn,
                "sse_algorithm": "aws:kms",
            },
        }
    ],
)

versioning = aws.s3.BucketVersioningV2(
    "mwaa-versioning",
    bucket=bucket.id,
    versioning_configuration={
        "status": "Enabled",
    },
)


allow_access_from_execution_role = aws.iam.get_policy_document_output(
    statements=[
        {
            "principals": [{"type": "AWS", "identifiers": [mwaa_execution_role.arn]}],
            "actions": ["s3:*"],
            "resources": [
                bucket.arn,
                bucket.arn.apply(lambda arn: f"{arn}/*"),
            ],
        }
    ]
)

bucket_policy = aws.s3.BucketPolicy(
    "bucket-policy", bucket=bucket.id, policy=allow_access_from_execution_role.json
)


log_groups = ["DAGProcessing", "Scheduler", "Task", "WebServer", "Worker"]

log_group_resources = []
for group in log_groups:
    name = f"airflow-my-airflow-env-{group}"
    log_group_resources.append(
        aws.cloudwatch.LogGroup(name, retention_in_days=1, name=name)
    )

requirements_file = aws.s3.BucketObjectv2(
    "requirements.txt",
    bucket=bucket.id,
    key="requirements.txt",
    source=pulumi.FileAsset("./airflow/requirements.txt"),
    kms_key_id=encryption_key.arn,
    server_side_encryption="aws:kms",
)

folder_name = "airflow/dags"

# Traverse the directory recursively
for root, dirs, files in os.walk(folder_name):
    for file in files:
        if not file.endswith(".pyc"):
            # Get the full file path
            file_path = os.path.join(root, file)

            # Construct the S3 key by removing the root folder path
            relative_path = os.path.relpath(file_path, folder_name)
            s3_key = f"dags/{relative_path}"

            # Create the S3 BucketObject for each file
            aws.s3.BucketObjectv2(
                s3_key,
                bucket=bucket.id,
                key=s3_key,
                source=pulumi.FileAsset(file_path),
                kms_key_id=encryption_key.arn,
                server_side_encryption="aws:kms",
            )


mwaa_environment = aws.mwaa.Environment(
    "airflow-environment",
    name="my-airflow-env",
    airflow_version="2.10.1",
    environment_class="mw1.small",
    execution_role_arn=mwaa_execution_role.arn,
    source_bucket_arn=bucket.arn,
    kms_key=encryption_key.arn,
    dag_s3_path="dags/",
    requirements_s3_path="requirements.txt",
    requirements_s3_object_version=requirements_file.version_id,
    network_configuration={
        "subnetIds": [private_subnet_1.id, private_subnet_2.id],
        "securityGroupIds": [security_group.id],
    },
    min_workers=2,
    max_workers=2,
    min_webservers=2,
    max_webservers=2,
    logging_configuration={
        "dag_processing_logs": {
            "enabled": True,
            "logLevel": "ERROR",
        },
        "task_logs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "webserver_logs": {
            "enabled": True,
            "logLevel": "CRITICAL",
        },
        "scheduler_logs": {
            "enabled": True,
            "logLevel": "ERROR",
        },
        "worker_logs": {
            "enabled": True,
            "logLevel": "DEBUG",
        },
    },
    webserver_access_mode="PUBLIC_ONLY",
    airflow_configuration_options={
        "logging.logging_level": "INFO",
        "core.parallelism": "100",
        "celery.worker_autoscale": "5,5",
        "core.max_active_tasks_per_dag": "50",
        "celery.sync_parallelism": "1",
        "scheduler.parsing_processes": "2",
        "core.min_serialized_dag_update_interval": "300",
        "scheduler.min_file_process_interval": "300",
        "scheduler.dag_dir_list_interval": "600",
        "celery.sync_parallelism": "1",
        "core.dag_file_processor_timeout": "100",
        "core.dagbag_import_timeout": "60",
    },
)

pulumi.export("dashboard_name", dashboard.dashboard_name)
