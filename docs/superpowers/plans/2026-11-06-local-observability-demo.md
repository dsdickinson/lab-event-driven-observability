# Local Observability Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local Compose order system whose SQL data, metrics, logs, traces, probes, Kafka events, and RabbitMQ tasks support an interview-ready Grafana investigation.

**Architecture:** FastAPI writes orders and outbox rows to PostgreSQL. A publisher emits Kafka events, a dispatcher turns them into RabbitMQ tasks, and a worker fulfills them. OpenTelemetry Collector routes signals to Prometheus, Loki, and Tempo; Grafana also reads PostgreSQL with SQL.

**Tech Stack:** Python 3.12, FastAPI, psycopg, confluent-kafka, pika, OpenTelemetry Python SDK, Docker Compose, PostgreSQL, Kafka, RabbitMQ, Prometheus, Loki, Tempo, Grafana.

**Spec:** `openspec/changes/local-observability-demo/design.md` and `openspec/changes/local-observability-demo/specs/`

## Global Constraints

- All runtime services run locally via Docker Compose.
- Kubernetes is deferred.
- Olist data is optional and not committed.
- Metrics have no order-ID labels.
- Message delivery is at least once; handlers are idempotent.

## Review Focus

- Kafka unavailable after order commit: pending outbox row survives and publishes later.
- Duplicate Kafka event: RabbitMQ task may repeat but fulfillment changes order once.
- Worker crash before acknowledgement: task redelivery does not duplicate the result.
- Empty PostgreSQL database on first boot: schema and fixture initialize deterministically.
- Grafana restart: provisioned SQL and telemetry data sources and dashboards reappear.

---

## File map

- `compose.yaml`: all local services, volumes, and health checks.
- `app/common.py`: environment configuration, database and broker connections, message IDs.
- `app/api.py`: HTTP order creation, health endpoint, order queries.
- `app/outbox.py`: pending event publisher.
- `app/dispatcher.py`: Kafka consumer and RabbitMQ task publisher.
- `app/worker.py`: idempotent fulfillment.
- `app/analytics.py`: independent Kafka consumer and aggregate.
- `app/traffic.py`: bounded generated fixture and live orders.
- `app/telemetry.py`: OpenTelemetry setup and context propagation.
- `db/init.sql`: order, outbox, fulfillment, and analytics schema.
- `observability/`: Prometheus, Collector, Blackbox, Loki, Tempo, and Grafana configuration and dashboard JSON.
- `tests/`: small unit tests for payload validation and idempotency, plus live smoke checks.
- `README.md`: operations, architecture, SQL/PromQL dashboard tour, and incident walkthroughs.

### Task 1: Core order flow

**Files:** `app/api.py`, `app/common.py`, `db/init.sql`, `tests/test_orders.py`

**Interfaces:** `POST /orders` accepts product ID and quantity and returns order ID; `GET /health` and `GET /orders/{id}` support probes and inspection.

- [ ] Write tests for invalid order input and atomic order/outbox persistence.
- [ ] Implement the API and schema.
- [ ] Run `python3 -m unittest discover -s tests` and confirm those tests pass.

### Task 2: Asynchronous delivery

**Files:** `app/outbox.py`, `app/dispatcher.py`, `app/worker.py`, `app/analytics.py`, `tests/test_delivery.py`

**Interfaces:** Kafka topic `orders.placed`; RabbitMQ queue `fulfillment`; stable `event_id` and `order_id` in each payload.

- [ ] Write duplicate-delivery and transient-failure tests.
- [ ] Implement acknowledged publishing, offset commits, worker idempotency, retry/dead-letter flow, and analytics consumption.
- [ ] Run `python3 -m unittest discover -s tests` and verify the failure cases pass.

### Task 3: Compose and telemetry

**Files:** `compose.yaml`, `app/telemetry.py`, `observability/*`, `tests/smoke.py`

**Interfaces:** OTLP on the Compose network; Prometheus scrapes app and exporters; Grafana data sources have fixed UIDs.

- [ ] Start Compose and verify required health endpoints and broker metrics.
- [ ] Add traces, structured logs, metrics, and message-header context propagation.
- [ ] Query Prometheus, Loki, and Tempo in a smoke check for a generated order.

### Task 4: Data and failure scenarios

**Files:** `app/traffic.py`, `app/import_olist.py`, `scripts/scenario.py`, `tests/test_import.py`

**Interfaces:** default traffic starts without downloaded data; optional importer reads local CSV files; scenarios can start and reset.

- [ ] Write tests for malformed/empty Olist input and scenario reset.
- [ ] Implement generated fixture, traffic, import, and slow/fail/pause controls.
- [ ] Verify each scenario changes the expected metric or queue state.

### Task 5: Dashboards and delivery

**Files:** `observability/grafana/**`, `README.md`, `tests/smoke.py`

**Interfaces:** Grafana dashboards use PromQL for operational metrics and SQL for order records; logs and traces are accessible from investigation paths.

- [ ] Provision data sources and dashboards for API, order flow, RabbitMQ, Kafka, and pipeline health.
- [ ] Verify panels against healthy and failing scenarios, including a SQL order breakdown.
- [ ] Document setup, reset, resource requirements, interview walkthrough, and deferred Kubernetes work.
- [ ] Run the full smoke check and `docker compose config` before completion.
