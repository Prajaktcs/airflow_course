import os
import json

import pulumi
import pulumi_aws as aws

from iam import mwaa_execution_role

vpc = aws.ec2.Vpc(
    "mwaa-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

internet_gateway = aws.ec2.InternetGateway(
    "internet-gateway", vpc_id=vpc.id, tags={"Name": "InternetGateway"}
)

# Create a public subnet in the VPC
public_subnet = aws.ec2.Subnet(
    "public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone="us-west-2a",
    map_public_ip_on_launch=True,  # Ensures instances in this subnet get a public IP
    tags={"Name": "PublicSubnet"},
)

public_subnet_2 = aws.ec2.Subnet(
    "public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone="us-west-2b",
    map_public_ip_on_launch=True,  # Ensures instances in this subnet get a public IP
    tags={"Name": "PublicSubnet"},
)

# Create a route table for the public subnet
public_route_table = aws.ec2.RouteTable(
    "public-route-table",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "gateway_id": internet_gateway.id}],
    tags={"Name": "PublicRouteTable"},
)

# Associate the public subnet with the public route table
public_route_table_assoc = aws.ec2.RouteTableAssociation(
    "public-subnet-route-association",
    subnet_id=public_subnet.id,
    route_table_id=public_route_table.id,
)

public_route_table_assoc_2 = aws.ec2.RouteTableAssociation(
    "public-subnet-2-route-association",
    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id,
)


private_subnet_1 = aws.ec2.Subnet(
    "private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone="us-west-2a",
)

private_subnet_2 = aws.ec2.Subnet(
    "private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone="us-west-2b",
)

nat_eip_a = aws.ec2.Eip("nat-eip-a", vpc=True)
nat_eip_b = aws.ec2.Eip("nat-eip-b", vpc=True)

nat_gateway_a = aws.ec2.NatGateway(
    "gateway-a", subnet_id=public_subnet.id, allocation_id=nat_eip_a.id
)

nat_gateway_b = aws.ec2.NatGateway(
    "gateway-b", subnet_id=public_subnet_2.id, allocation_id=nat_eip_b.id
)


# Create a route table for the private subnets
private_route_table_a = aws.ec2.RouteTable(
    "private-route-table-a",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway_a.id}],
    tags={"Name": "PrivateRouteTable"},
)

private_route_table_b = aws.ec2.RouteTable(
    "private-route-table-b",
    vpc_id=vpc.id,
    routes=[{"cidr_block": "0.0.0.0/0", "nat_gateway_id": nat_gateway_b.id}],
    tags={"Name": "PrivateRouteTable"},
)

# Associate the route table with the private subnets
private_subnet_1_route_assoc = aws.ec2.RouteTableAssociation(
    "private-subnet-1-route-association",
    subnet_id=private_subnet_1.id,
    route_table_id=private_route_table_a.id,
)

private_subnet_2_route_assoc = aws.ec2.RouteTableAssociation(
    "private-subnet-2-route-association",
    subnet_id=private_subnet_2.id,
    route_table_id=private_route_table_b.id,
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
            "cidr_blocks": ["49.36.40.176/32"],
        },
        # Allow inbound traffic on port 443 (HTTPS)
        {
            "protocol": "tcp",
            "from_port": 443,
            "to_port": 443,
            "cidr_blocks": ["49.36.40.176/32"],
        },
        # Allow access to postgres
        {"protocol": "tcp", "from_port": 5432, "to_port": 5432, "self": True},
        {"protocol": "all", "from_port": 0, "to_port": 0, "self": True},
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
