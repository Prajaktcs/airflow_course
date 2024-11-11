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
                ["AWS/MWAA", "SchedulerHeartbeat", "Environment", "my-airflow-env"]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Sum"
        }
    },
    {
        "type": "metric",
        "x": 0,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "Worker Task Success Rate",
            "metrics": [
                ["AWS/MWAA", "WorkerSuccess", "Environment", "my-airflow-env"]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Sum"
        }
    },
    {
        "type": "metric",
        "x": 12,
        "y": 0,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "DAG Processing Times",
            "metrics": [
                ["AWS/MWAA", "DAGProcessingTime", "Environment", "my-airflow-env"]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Average"
        }
    },
    {
        "type": "metric",
        "x": 12,
        "y": 6,
        "width": 12,
        "height": 6,
        "properties": {
            "title": "Scheduler Delay",
            "metrics": [
                ["AWS/MWAA", "SchedulerDelay", "Environment", "my-airflow-env"]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Average"
        }
    },
    {
        "type": "metric",
        "x": 0,
        "y": 12,
        "width": 24,
        "height": 6,
        "properties": {
            "title": "Task Failures",
            "metrics": [
                ["AWS/MWAA", "FailedTasks", "Environment", "my-airflow-env"]
            ],
            "view": "timeSeries",
            "stacked": False,
            "region": "us-west-2",
            "period": 300,
            "stat": "Sum"
        }
    }
]

# Create the CloudWatch Dashboard
dashboard = aws.cloudwatch.Dashboard(
    "mwaaDashboard",
    dashboard_name="MWAADashboard",
    dashboard_body=pulumi.Output.all().apply(lambda _: json.dumps({
        "widgets": widgets
    }))
)


