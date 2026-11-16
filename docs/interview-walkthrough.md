# Ten-minute interview walkthrough

## 1. Explain the architecture (1 minute)

Show the diagram in the [README](../README.md). The API commits an order and outbox row atomically. The outbox publisher sends a fact to Kafka. Two consumer groups read it independently: analytics updates an aggregate, and the dispatcher creates a RabbitMQ fulfillment task. A worker completes the task and records the result in PostgreSQL. At-least-once delivery means duplicates can occur; stable event IDs make the worker idempotent.

## 2. Show a healthy order (2 minutes)

Run `docker compose run --rm api python -m app.smoke`. Point out the order ID and trace ID. Open Grafana's **02 Order Flow and SQL** dashboard. The SQL tables answer what persisted in PostgreSQL; the PromQL graph answers how the service is behaving over time. Open Tempo with the trace ID and show spans from the API, outbox publisher, dispatcher, worker, and analytics consumer. Search Loki for the order ID.

## 3. Create an incident (3 minutes)

Run `python3 scripts/scenario.py fulfillment-backlog`. In **03 RabbitMQ Fulfillment**, watch ready tasks rise. In **04 Kafka Events**, the dispatcher can remain caught up, showing that the bottleneck is downstream of Kafka. In **02 Order Flow and SQL**, new orders remain in `placed` status. Restore with `python3 scripts/scenario.py baseline` and watch the backlog drain.

## 4. Demonstrate query choices (2 minutes)

Prometheus stores operational time series. A PromQL expression such as `sum(rate(demo_orders_created_total[5m]))` shows order creation rate. PostgreSQL stores business records. SQL such as `SELECT status, count(*) FROM orders GROUP BY status` shows current persisted state. Loki uses LogQL for logs, and Tempo uses TraceQL or trace ID lookup. Grafana's data source determines the query language used by a panel.

## 5. Discuss production tradeoffs (2 minutes)

- The demo uses single-node brokers and local volumes. Production would need durability, backups, access control, and high availability.
- Kafka facts are retained and independently consumed; RabbitMQ handles work tasks and retries. Both are used intentionally, although a smaller real application could use one broker.
- The outbox avoids losing events when an order commits but Kafka is unavailable. Acknowledgement gaps still allow duplicate delivery, so consumers must be idempotent.
- Trace context is carried in message headers, while order IDs stay in logs and traces rather than high-cardinality metric labels.
- The default data is synthetic, with an optional Olist product import. The generated traffic creates fresh telemetry for repeatable investigations.
- Kubernetes deployment and cluster monitoring are a later extension; Docker Compose keeps this version reproducible on a laptop.
