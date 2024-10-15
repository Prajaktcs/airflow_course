import pulumi
import pulumi_aws as aws

# Step 1: Create a VPC for the Airflow environment
vpc = aws.ec2.Vpc(
    "airflow-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

# Step 2: Create subnets within the VPC
subnet1 = aws.ec2.Subnet(
    "airflow-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
)

subnet2 = aws.ec2.Subnet(
    "airflow-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-east-1b",
)

# Step 3: Create an S3 bucket for MWAA logs and DAGs
mwaa_bucket = aws.s3.Bucket("airflow-dag-bucket")

# Step 4: Create IAM Roles for MWAA
mwaa_execution_role = aws.iam.Role(
    "airflow-execution-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": ["airflow.amazonaws.com","airflow-env.amazonaws.com"]

                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }""",
)

# Step 5: Attach policies to the IAM Role
iam_policy_attachment = aws.iam.RolePolicyAttachment(
    "airflow-policy-attachment",
    role=mwaa_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess",
)

# Step 6: Create the MWAA environment
mwaa_environment = aws.mwaa.Environment(
    "airflow-environment",
    name="my-airflow-env",
    airflow_version="2.9.2",
    environment_class="mw1.small",
    execution_role_arn=mwaa_execution_role.arn,
    source_bucket_arn=mwaa_bucket.arn,
    dag_s3_path="dags/",
    network_configuration={
        "subnetIds": [subnet1.id, subnet2.id],
        "securityGroupIds": [vpc.default_security_group_id],
    },
    logging_configuration={
        "dagProcessingLogs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "taskLogs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "webserverLogs": {
            "enabled": True,
            "logLevel": "INFO",
        },
        "schedulerLogs": {
            "enabled": True,
            "logLevel": "INFO",
        },
    },
    webserver_access_mode="PUBLIC_ONLY",
)

# Output the MWAA environment details
pulumi.export("airflowEnvironmentName", mwaa_environment.name)
pulumi.export("dagBucketName", mwaa_bucket.bucket)
