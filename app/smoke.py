"""End-to-end smoke check; run inside Compose: docker compose run --rm api python -m app.smoke"""
import time

import requests

from app.common import db


def wait_until(label, check, timeout=90):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                print(f"PASS {label}: {result}")
                return result
        except Exception as error:
            last = error
        time.sleep(3)
    raise AssertionError(f"{label} not ready after {timeout}s; last error: {last}")


def prom(query):
    response = requests.get("http://prometheus:9090/api/v1/query", params={"query": query}, timeout=10)
    response.raise_for_status()
    return response.json()["data"]["result"]


def main():
    response = requests.post("http://api:8000/orders", json={"product_id": "coffee", "quantity": 2}, timeout=15)
    response.raise_for_status()
    data = response.json()
    order_id, trace_id = data["order_id"], data["trace_id"]
    print(f"Created order {order_id}; trace {trace_id}")

    def finished():
        result = requests.get(f"http://api:8000/orders/{order_id}", timeout=10).json()
        return result["status"] == "fulfilled"

    wait_until("order fulfilled", finished)

    def delivered():
        with db() as conn:
            row = conn.execute("SELECT o.published_at, a.event_id FROM outbox o LEFT JOIN analytics_events a USING (event_id) WHERE o.order_id=%s", (order_id,)).fetchone()
        return row and row[0] and row[1]

    wait_until("Kafka and analytics processed", delivered)
    wait_until("application metric", lambda: prom("lab_orders_created_total"))
    wait_until("RabbitMQ metric", lambda: prom("rabbitmq_queue_messages_ready"))
    wait_until("Kafka lag metric", lambda: prom("kafka_consumergroup_lag_sum"))
    wait_until("blackbox probe", lambda: prom("probe_success{job=\"blackbox\"}"))
    wait_until("Collector scrape", lambda: prom("up{job=\"otel-collector\"}"))

    def log_visible():
        result = requests.get("http://loki:3100/loki/api/v1/query_range",
                              params={"query": f'{{service_name="order-api"}} |= "{order_id}"', "limit": 5}, timeout=10)
        result.raise_for_status()
        return bool(result.json()["data"]["result"])

    wait_until("order log in Loki", log_visible)

    def trace_visible():
        result = requests.get(f"http://tempo:3200/api/traces/{trace_id}", timeout=10)
        if result.status_code == 404:
            return False
        result.raise_for_status()
        services = {
            item["value"].get("stringValue")
            for batch in result.json().get("batches", [])
            for item in batch.get("resource", {}).get("attributes", [])
            if item.get("key") == "service.name"
        }
        expected = {"order-api", "outbox-publisher", "order-dispatcher", "fulfillment-worker", "analytics-consumer"}
        return sorted(services) if expected.issubset(services) else False

    wait_until("order trace in Tempo", trace_visible)
    from app.worker import apply_fulfillment
    with db() as conn:
        event_id = conn.execute("SELECT event_id FROM outbox WHERE order_id=%s", (order_id,)).fetchone()[0]
    assert apply_fulfillment(event_id, order_id) is False
    print("PASS duplicate fulfillment ignored")
    print("PASS all smoke checks")


if __name__ == "__main__":
    main()
