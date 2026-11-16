## Why

Build a portfolio-quality, fully local observability project that demonstrates how to design an application, instrument it, operate two messaging systems, and investigate incidents in Grafana. Existing demos are useful references, but building the application and dashboards here makes the architecture and operational choices explainable in a job setting.

## What Changes

- Add a Docker Compose application and observability environment with Grafana, Prometheus, Blackbox Exporter, OpenTelemetry Collector, Loki, Tempo, RabbitMQ, Kafka, and PostgreSQL.
- Build an order workflow: persist an order and outbox event; publish the event to Kafka; consume it and enqueue RabbitMQ fulfillment tasks; process tasks and update order state.
- Add an initial generated fixture and controllable live traffic. Support an optional, separately downloaded Olist e-commerce data import after the core flow works.
- Instrument services and brokers so metrics, logs, traces, probes, queue depth, and consumer lag can be examined together.
- Provision Grafana data sources and build dashboards with PromQL metrics panels, SQL order-data panels, drill-down links, and repeatable failure scenarios.
- Document setup, validation, and incident walkthroughs. Defer Kubernetes deployment and cluster monitoring to a future change.

## Capabilities

### New Capabilities

- `local-environment`: Start, stop, and inspect the entire local stack through Docker Compose.
- `order-workflow`: Create orders and process Kafka events and RabbitMQ fulfillment tasks reliably.
- `test-data-and-scenarios`: Seed representative data, generate traffic, and trigger repeatable operational scenarios.
- `telemetry-pipeline`: Collect application and infrastructure signals into Prometheus, Loki, and Tempo, including local blackbox probes.
- `grafana-investigation`: Explore provisioned PromQL and SQL dashboards and correlate panels, logs, and traces during an incident.

### Modified Capabilities

None.

## Impact

This is a new project. It adds application services, Compose and service configuration, data generation/import tooling, Grafana provisioning and dashboard definitions, verification scripts, and user documentation. Docker and Docker Compose are required locally; the optional Olist import requires the user to obtain that dataset separately under its published license.
