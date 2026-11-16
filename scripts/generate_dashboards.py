"""Generate version-controlled Grafana dashboards for the local demo."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "observability/grafana/dashboards"


def panel(title, datasource, query, x, y, kind="timeseries", unit="short", width=12, height=8):
    source_type = {"postgres": "postgres", "loki": "loki"}.get(datasource, "prometheus")
    target = {"refId": "A", "datasource": {"type": source_type, "uid": datasource}}
    if datasource == "postgres":
        target.update({"rawSql": query, "format": "table" if kind == "table" else "time_series", "rawQuery": True})
    elif datasource == "loki":
        target.update({"expr": query, "queryType": "range"})
    else:
        target.update({"expr": query, "legendFormat": "{{service_name}} {{result}} {{queue}} {{consumergroup}} {{job}}"})
    return {
        "id": y * 10 + x + 1,
        "title": title,
        "type": kind,
        "datasource": {"type": source_type, "uid": datasource},
        "targets": [target],
        "gridPos": {"x": x, "y": y, "w": width, "h": height},
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": {"showHeader": True} if kind == "table" else {},
    }


def dashboard(uid, title, description, panels):
    return {"uid": uid, "title": title, "description": description, "schemaVersion": 41,
            "version": 1, "refresh": "10s", "timezone": "browser", "tags": ["local-demo"],
            "time": {"from": "now-1h", "to": "now"}, "panels": panels}


dashboards = [
    dashboard("demo-api", "01 Service and API Health", "PromQL service and HTTP metrics", [
        panel("Orders per second (PromQL)", "prometheus", "sum(rate(demo_http_requests_total{route=\"/orders\"}[5m]))", 0, 0, unit="reqps"),
        panel("API errors per second (PromQL)", "prometheus", "sum(rate(demo_http_requests_total{route=\"/orders\",result!=\"created\"}[5m])) or vector(0)", 12, 0, unit="reqps"),
        panel("p95 order API latency (PromQL)", "prometheus", "histogram_quantile(0.95, sum by (le) (rate(demo_http_duration_seconds_bucket{route=\"/orders\"}[5m])))", 0, 8, unit="s"),
        panel("API probe success (PromQL)", "prometheus", "probe_success{job=\"blackbox\"}", 12, 8),
        panel("Recent API logs (LogQL)", "loki", "{service_name=\"order-api\"}", 0, 16, kind="logs", width=24),
    ]),
    dashboard("demo-orders", "02 Order Flow and SQL", "Compare Prometheus operations with PostgreSQL business records", [
        panel("Orders created per second (PromQL)", "prometheus", "sum(rate(demo_orders_created_total[5m]))", 0, 0, unit="ops"),
        panel("Pending outbox events (SQL)", "postgres", "SELECT count(*) AS pending_events FROM outbox WHERE published_at IS NULL", 12, 0, kind="table"),
        panel("Orders by status (SQL)", "postgres", "SELECT status, count(*) AS orders FROM orders GROUP BY status ORDER BY status", 0, 8, kind="table"),
        panel("Recent orders (SQL)", "postgres", "SELECT created_at, id, product_id, quantity, amount_cents, status FROM orders ORDER BY created_at DESC LIMIT 20", 12, 8, kind="table"),
        panel("Fulfillment time by order (SQL)", "postgres", "SELECT id, extract(epoch FROM fulfilled_at - created_at) AS fulfillment_seconds FROM orders WHERE fulfilled_at IS NOT NULL ORDER BY fulfilled_at DESC LIMIT 20", 0, 16, kind="table"),
        panel("Outbox oldest pending age (SQL)", "postgres", "SELECT COALESCE(extract(epoch FROM now() - min(created_at)), 0) AS seconds FROM outbox WHERE published_at IS NULL", 12, 16, kind="table"),
    ]),
    dashboard("demo-rabbit", "03 RabbitMQ Fulfillment", "Queue and worker health", [
        panel("Ready tasks (PromQL)", "prometheus", "rabbitmq_queue_messages_ready{queue=~\"fulfillment.*\"}", 0, 0),
        panel("Unacknowledged tasks (PromQL)", "prometheus", "rabbitmq_queue_messages_unacked{queue=\"fulfillment\"}", 12, 0),
        panel("Fulfilled orders per second (PromQL)", "prometheus", "sum(rate(demo_orders_fulfilled_total[5m]))", 0, 8, unit="ops"),
        panel("Fulfillment failures per second (PromQL)", "prometheus", "sum(rate(demo_fulfillment_failures_total[5m])) or vector(0)", 12, 8, unit="ops"),
    ]),
    dashboard("demo-kafka", "04 Kafka Events", "Topic progress and consumer lag", [
        panel("Order topic offset (PromQL)", "prometheus", "sum(kafka_topic_partition_current_offset{topic=\"orders.placed\"})", 0, 0),
        panel("Consumer lag (PromQL)", "prometheus", "kafka_consumergroup_lag_sum{topic=\"orders.placed\"}", 12, 0),
        panel("Outbox publish rate (PromQL)", "prometheus", "sum(rate(demo_outbox_published_total[5m]))", 0, 8, unit="ops"),
        panel("Analytics consumption rate (PromQL)", "prometheus", "sum(rate(demo_analytics_orders_total[5m]))", 12, 8, unit="ops"),
    ]),
    dashboard("demo-pipeline", "05 Telemetry Pipeline", "Scrape, probe, and backend availability", [
        panel("Prometheus target health (PromQL)", "prometheus", "up", 0, 0),
        panel("Collector accepted spans (PromQL)", "prometheus", "sum(rate(otelcol_receiver_accepted_spans_total[5m]))", 12, 0, unit="ops"),
        panel("Collector refused records (PromQL)", "prometheus", "(sum(rate(otelcol_receiver_refused_spans_total[5m])) or vector(0)) + (sum(rate(otelcol_receiver_refused_log_records_total[5m])) or vector(0))", 0, 8, unit="ops"),
        panel("Blackbox duration (PromQL)", "prometheus", "probe_duration_seconds{job=\"blackbox\"}", 12, 8, unit="s"),
        panel("Loki lines received per second (PromQL)", "prometheus", "sum(rate(loki_distributor_lines_received_total[5m]))", 0, 16, unit="ops"),
        panel("Tempo spans received per second (PromQL)", "prometheus", "sum(rate(tempo_distributor_spans_received_total[5m]))", 12, 16, unit="ops"),
    ]),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for item in dashboards:
        path = OUT / f"{item['uid']}.json"
        path.write_text(json.dumps(item, indent=2) + "\n")
        print(path)


if __name__ == "__main__":
    main()
