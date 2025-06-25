# app/services/metrics.py
from azure.monitor.query import MetricsQueryClient, MetricAggregationType
from app.services.auth import get_credentials
from datetime import timedelta

def get_cpu_usage(resource_id):
    cred = get_credentials()
    client = MetricsQueryClient(cred)
    response = client.query_resource(
        resource_id=resource_id,
        metric_names=["Percentage CPU"],
        timespan=timedelta(hours=24),
        aggregations=[MetricAggregationType.AVERAGE]
    )
    try:
        data = response.metrics[0].timeseries[0].data
        return data[-1].average if data else None
    except:
        return None
