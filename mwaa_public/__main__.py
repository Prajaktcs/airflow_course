import os
import json

import pulumi
import pulumi_aws as aws

from iam import mwaa_execution_role
from network import private_subnet_1, private_subnet_2


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

for file in os.listdir(folder_name):
    file_path = os.path.join(folder_name, file)
    if os.path.isfile(file_path):
        aws.s3.BucketObjectv2(
            f"dags/{file}",
            bucket=bucket.id,
            key=f"dags/{file}",
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
    max_workers=2,
    min_webservers=2,
    max_webservers=2,
    logging_configuration={
        "dag_processing_logs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "task_logs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "webserver_logs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "scheduler_logs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "worker_logs": {
            "enabled": True,
            "logLevel": "INFO",
        },
    },
    webserver_access_mode="PUBLIC_ONLY",
    airflow_configuration_options={"logging.logging_level": "INFO"},
)
