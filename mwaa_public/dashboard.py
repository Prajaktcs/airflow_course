import json

import pulumi
import pulumi_aws as aws


ENVIRONMENT_NAME = "my-airflow-env"


# BaseWorker metric
base_worker_metric = {
    "id": "m1",
    "label": "Base Worker",
    "metricStat": {
        "metric": {
            "namespace": "AWS/MWAA",
            "metricName": "CPUUtilization",
            "dimensions": {
                "Cluster": "BaseWorker",
                "Environment": ENVIRONMENT_NAME,
            },
        },
        "period": 60,
        "stat": "SampleCount",
    },
}

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
                    "aurora_to_redshift",
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
        "width": 12,
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
                    "aurora_to_redshift",
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
            "view": "timeSeries",
            "title": "Running Tasks",
            "metrics": [
                [
                    "AmazonMWAA",
                    "RunningTasks",
                    "Environment",
                    "my-airflow-env",
                    "Function",
                    "Executor",
                ]
            ],
            "stat": "Average",
            "region": aws.config.region,
            "period": 300,
        },
    },
    {
        "type": "metric",
        "x": 12,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "title": "Queued Tasks",
            "metrics": [
                [
                    "AmazonMWAA",
                    "QueuedTasks",
                    "Environment",
                    "my-airflow-env",
                    "Function",
                    "Executor",
                ]
            ],
            "stat": "Average",
            "region": aws.config.region,
            "period": 300,
        },
    },
    {
        "type": "metric",
        "x": 0,
        "y": 12,
        "width": 12,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "title": "Worker Slots Available",
            "metrics": [
                [
                    "AmazonMWAA",
                    "OpenSlots",
                    "Environment",
                    "my-airflow-env",
                    "Function",
                    "Executor",
                ]
            ],
            "stat": "Average",
            "region": aws.config.region,
            "period": 300,
        },
    },
    {
        "type": "metric",
        "x": 12,
        "y": 12,
        "width": 12,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "title": "CPUUtilization",
            "metrics": [
                [
                    "AWS/MWAA",
                    "CPUUtilization",
                    "Cluster",
                    "BaseWorker",
                    "Environment",
                    "my-airflow-env",
                ],
                ["...", "AdditionalWorker", ".", "."],
                ["...", "Scheduler", ".", "."],
                ["...", "WebServer", ".", "."],
                ["...", "DatabaseRole", "WRITER", ".", "."],
                ["...", "READER", ".", "."],
            ],
            "stat": "Average",
            "region": aws.config.region,
            "period": 300,
        },
    },
    {
        "type": "metric",
        "x": 12,
        "y": 12,
        "width": 12,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "title": "MemoryUtilization",
            "metrics": [
                [
                    "AWS/MWAA",
                    "MemoryUtilization",
                    "Cluster",
                    "BaseWorker",
                    "Environment",
                    "my-airflow-env",
                ],
                ["...", "AdditionalWorker", ".", "."],
                ["...", "Scheduler", ".", "."],
                ["...", "WebServer", ".", "."],
            ],
            "stat": "Average",
            "region": aws.config.region,
            "period": 300,
        },
    },
    {
        "type": "metric",
        "x": 0,
        "y": 12,
        "width": 12,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "title": "Slot Pools",
            "metrics": [
                [
                    "AmazonMWAA",
                    "PoolScheduledSlots",
                    "Environment",
                    "my-airflow-env",
                    "Pool",
                    "default_pool",
                ],
                [".", "PoolRunningSlots", ".", ".", ".", "."],
                [".", "PoolOpenSlots", ".", ".", ".", "."],
                [".", "PoolQueuedSlots", ".", ".", ".", "."],
            ],
            "stat": "Average",
            "region": aws.config.region,
            "period": 300,
        },
    },
    {
        "type": "metric",
        "x": 12,
        "y": 12,
        "width": 12,
        "height": 6,
        "properties": {
            "view": "timeSeries",
            "title": "Worker Count",
            "metrics": [
                [{"expression": "SUM(METRICS())", "label": "Expression1", "id": "e1"}],
                [
                    "AWS/MWAA",
                    "CPUUtilization",
                    "Cluster",
                    "AdditionalWorker",
                    "Environment",
                    "my-airflow-env",
                    {"id": "m1"},
                ],
                ["...", "BaseWorker", ".", ".", {"id": "m2"}],
            ],
            "stat": "SampleCount",
            "region": aws.config.region,
            "period": 60,
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
