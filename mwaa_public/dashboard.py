import json

import pulumi
import pulumi_aws as aws

# Define metrics widgets for the dashboard
widgets = [
    {
        "type": "metric",
        "x": 0,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "Scheduler Heartbeat",
            "metrics": [
                [
                    "AmazonMWAA",
                    "SchedulerHeartbeat",
                    "Function",
                    "Scheduler",
                    "Environment",
                    "my-airflow-env",
                ]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Sum",
        },
    },
    {
        "type": "metric",
        "x": 0,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "Celery Worker Heartbeat",
            "metrics": [
                [
                    "AmazonMWAA",
                    "CeleryWorkerHeartbeat",
                    "Function",
                    "Celery",
                    "Environment",
                    "my-airflow-env",
                ]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Sum",
        },
    },
    {
        "type": "metric",
        "x": 12,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "ETL DAG Success Time",
            "metrics": [
                [
                    "AmazonMWAA",
                    "DAGDurationSuccess",
                    "Environment",
                    "my-airflow-env",
                    "DAG",
                    "aurora_to_redshift"
                ]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Average",
        },
    },
    {
        "type": "metric",
        "x": 12,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "Scheduler Loop Duration",
            "metrics": [
                [
                    "AmazonMWAA",
                    "SchedulerLoopDuration",
                    "Function",
                    "Scheduler",
                    "Environment",
                    "my-airflow-env",
                ]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Average",
        },
    },
    {
        "type": "metric",
        "x": 0,
        "y": 12,
        "width": 24,
        "height": 6,
        "properties": {
            "title": "ETL DAG Failure Duration",
            "metrics": [
                [
                    "AmazonMWAA",
                    "DAGDurationFailed",
                    "Environment",
                    "my-airflow-env",
                    "DAG",
                    "aurora_to_redshift"
                ]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Sum",
        },
    },
]

# Create the CloudWatch Dashboard
dashboard = aws.cloudwatch.Dashboard(
    "mwaaDashboard",
    dashboard_name="MWAADashboard",
    dashboard_body=pulumi.Output.all().apply(
        lambda _: json.dumps({"widgets": widgets})
    ),
)
