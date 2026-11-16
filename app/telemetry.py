import logging
import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.view import (
    ExplicitBucketHistogramAggregation,
    View,
)


def setup(service):
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318")
    resource = Resource.create({"service.name": service, "deployment.environment": "local"})
    traces = TracerProvider(resource=resource)
    traces.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    trace.set_tracer_provider(traces)
    logs = LoggerProvider(resource=resource)
    logs.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=f"{endpoint}/v1/logs")))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(LoggingHandler(logger_provider=logs))
    reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=f"{endpoint}/v1/metrics"),
        export_interval_millis=10000,
    )
    views = [
        View(
            instrument_name="lab_http_duration",
            aggregation=ExplicitBucketHistogramAggregation(
                boundaries=[
                    0.05, 0.1, 0.25, 0.5, 0.75,
                    1.0, 1.25, 1.5, 2.0, 2.5, 5.0,
                ]
            ),
        )
    ]
    metrics.set_meter_provider(
        MeterProvider(resource=resource, metric_readers=[reader], views=views)
    )
    if not any(isinstance(handler, logging.StreamHandler) and not isinstance(handler, LoggingHandler) for handler in root.handlers):
        root.addHandler(logging.StreamHandler())
    return trace.get_tracer(service), metrics.get_meter(service)
