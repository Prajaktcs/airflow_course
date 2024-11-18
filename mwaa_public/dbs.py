import json

import pulumi
import pulumi_aws as aws

from network import private_subnet_1, private_subnet_2, private_subnet_3, vpc

current = aws.get_caller_identity()

db_security_group = aws.ec2.SecurityGroup(
    "db-security-group",
    vpc_id=vpc.id,
    description="security group for database",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 5432,
            "to_port": 5432,
            "cidr_blocks": [private_subnet_1.cidr_block, private_subnet_2.cidr_block],
        },
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
)

# Aurora Serverless Database Cluster (PostgreSQL)
aurora_cluster = aws.rds.Cluster(
    "aurora-serverless",
    engine="aurora-postgresql",
    engine_mode="serverless",
    scaling_configuration={
        "auto_pause": True,
        "min_capacity": 2,
        "max_capacity": 2,
        "seconds_until_auto_pause": 300,  # Set auto-pause timeout (5 mins)
    },
    database_name="my_database",
    master_username="airflow",
    master_password="SecurePassword123!",  # Update with a secure password
    skip_final_snapshot=True,
    vpc_security_group_ids=[db_security_group.id],
    db_subnet_group_name=aws.rds.SubnetGroup(
        "aurora-subnet-group",
        subnet_ids=[private_subnet_1.id, private_subnet_2.id],
    ).name,
)

# S3 Bucket for Data Exchange
data_exchange_bucket = aws.s3.Bucket(
    "data-exchange-bucket",
    bucket=f"my-data-exchange-bucket-{current.account_id}",
    force_destroy=True,  # Destroys all objects in bucket if bucket is deleted
)

# Enable S3 Bucket Encryption
bucket_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "bucketEncryption",
    bucket=data_exchange_bucket.id,
    rules=[
        {
            "applyServerSideEncryptionByDefault": {
                "sseAlgorithm": "AES256",  # Use AES256 for encryption
            },
        }
    ],
)

access_to_data_exchange_bucket = aws.iam.get_policy_document_output(
    statements=[
        {
            "actions": ["s3:*"],
            "resources": [
                data_exchange_bucket.arn,
                data_exchange_bucket.arn.apply(lambda arn: f"{arn}/*"),
            ],
        }
    ]
)


# Grant Redshift Access to S3 Bucket
redshift_s3_policy = aws.iam.Policy(
    "redshiftS3Policy", policy=access_to_data_exchange_bucket.json
)

# Attach Policy to Redshift IAM Role
redshift_role = aws.iam.Role(
    "redshiftS3Role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "redshift.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)

redshift_role_policy_attachment = aws.iam.RolePolicyAttachment(
    "redshiftS3RoleAttachment",
    role=redshift_role.name,
    policy_arn=redshift_s3_policy.arn,
)


# Redshift Serverless Workgroup
redshift_namespace = aws.redshiftserverless.Namespace(
    "redshift-namespace",
    namespace_name="my-redshift-namespace",
    db_name="my_redshift_db",
    admin_username="admin",
    admin_user_password="SecurePassword123!",  # Update with a secure password
    iam_roles=[redshift_role.arn],
)

redshift_security_group = aws.ec2.SecurityGroup(
    "redshift-security-group",
    vpc_id=vpc.id,
    description="security group for database",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 5439,
            "to_port": 5439,
            "cidr_blocks": [private_subnet_1.cidr_block, private_subnet_2.cidr_block],
        },
        {
            "protocol": "tcp",
            "from_port": 5439,
            "to_port": 5439,
            "self": True,
        },
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]},
    ],
)


redshift_workgroup = aws.redshiftserverless.Workgroup(
    "redshift-workgroup",
    workgroup_name="my-redshift-workgroup",
    namespace_name=redshift_namespace.namespace_name,
    base_capacity=8,  # Serverless resource capacity, choose appropriate range
    publicly_accessible=False,
    security_group_ids=[redshift_security_group.id],
    subnet_ids=[private_subnet_1.id, private_subnet_2.id, private_subnet_3],
)
