import pulumi_aws as aws

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

cloudwatch_policy_attachement = aws.iam.RolePolicyAttachment(
    "airflow-cloudwatch",
    role=mwaa_execution_role.name,
    policy_arn="arn:aws:iam::aws:policy/CloudWatchFullAccessV2",
)
