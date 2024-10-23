"""An AWS Python Pulumi program"""

import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc(
    "mwaa-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

private_subnet_1 = aws.ec2.Subnet(
    "private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="us-east-1a",
)

private_subnet_2 = aws.ec2.Subnet(
    "private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="us-east-1b",
)

security_group = aws.ec2.SecurityGroup(
    "airflow-security-group",
    vpc_id=vpc.id,
    description="Allow inbound traffic for Airflow environment",
    ingress=[
        # Allow inbound traffic on port 80 (HTTP)
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        # Allow inbound traffic on port 443 (HTTPS)
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["0.0.0.0/0"],
        },
        # Allow access to postgres
        {"protocol": "tcp", "from_port": 5432, "to_port": 5432, "self": True},
    ],
    egress=[
        # Allow all outbound traffic
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)


bucket = aws.s3.Bucket(
    "mwaa-bucket", acl="private", force_destroy=True, versioning={"enabled": True}
)

# IAM role
mwaa_execution_role = aws.iam.Role(
    "airflow-execution-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": ["airflow.amazonaws.com", "airflow-env.amazonaws.com"]
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }""",
)

iam_policy_attachment = aws.iam.RolePolicyAttachment(
    "airflow-policy-attachment",
    role=mwaa_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/AmazonS3FullAccess",
)

admin_policy_attachment = aws.iam.RolePolicyAttachment(
    "airflow-admin",
    role=mwaa_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/AdministratorAccess",
)

mwaa_environment = aws.mwaa.Environment(
    "airflow-environment",
    name="my-airflow-env",
    airflow_version="2.10.1",
    environment_class="mw1.small",
    execution_role_arn=mwaa_execution_role.arn,
    source_bucket_arn=bucket.arn,
    dag_s3_path="dags/",
    network_configuration={
        "subnetIds": [private_subnet_1.id, private_subnet_2.id],
        "securityGroupIds": [security_group.id],
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
