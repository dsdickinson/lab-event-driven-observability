## 1. Local foundation

- [x] 1.1 Create the Python service layout, shared configuration and contracts, and pinned dependencies.
- [x] 1.2 Add Docker Compose services, networks, named volumes, health checks, and pinned images for PostgreSQL, Kafka, RabbitMQ, and the application.
- [x] 1.3 Add deterministic PostgreSQL schema creation and Kafka topic and RabbitMQ queue setup.
- [x] 1.4 Document startup, shutdown, restart, and intentional data reset; verify persistence across a restart.

## 2. Order and messaging workflow

- [x] 2.1 Implement the Order API and transactional order-plus-outbox write with input validation and stable IDs.
- [x] 2.2 Implement an outbox publisher that waits for Kafka acknowledgement and retries pending events.
- [x] 2.3 Implement a Kafka dispatcher that publishes confirmed RabbitMQ fulfillment tasks before committing offsets.
- [x] 2.4 Implement a fulfillment worker with duplicate-safe state changes, bounded retries, and dead-letter visibility.
- [x] 2.5 Implement an independent Kafka analytics consumer and expose its aggregate and lag.
- [x] 2.6 Verify order completion, Kafka downtime recovery, and duplicate event or task delivery.

## 3. Telemetry backends and instrumentation

- [x] 3.1 Add Grafana, Prometheus, Blackbox Exporter, OpenTelemetry Collector, Loki, and Tempo Compose services and configuration.
- [x] 3.2 Instrument application HTTP, database, Kafka, RabbitMQ, and worker operations with metrics, structured logs, traces, and message-header context propagation.
- [x] 3.3 Configure Collector routing to Prometheus scrape endpoint, Loki, and Tempo; add RabbitMQ, Kafka, and component-health metric scrapes.
- [x] 3.4 Add local API blackbox probe and verify metrics, logs, trace spans, broker backlog metrics, and probe results reach their backends.

## 4. Workloads and incident exercises

- [x] 4.1 Add an invented default fixture and bounded live traffic generator; verify dashboards receive data after startup.
- [x] 4.2 Add repeatable slow-API, API-down, fulfillment-backlog, Kafka-lag, and failed-fulfillment scenarios with reset instructions.
- [x] 4.3 Add the optional importer for user-supplied Olist files with validation and license/source documentation.

## 5. Grafana dashboards

- [x] 5.1 Provision Prometheus, Loki, Tempo, and read-only PostgreSQL data sources and version-controlled dashboard folders.
- [x] 5.2 Build service/API health and order-flow dashboards with PromQL RED and outbox panels plus SQL order-count, status, and fulfillment panels.
- [x] 5.3 Build RabbitMQ and Kafka dashboards with depth, failures, throughput, and consumer-lag panels.
- [x] 5.4 Build telemetry pipeline health dashboard with scrape, Collector, backend ingest, and Blackbox probe panels.
- [x] 5.5 Add metric-to-log and trace investigation paths and verify the failed-order walkthrough end to end.

## 6. Delivery verification

- [x] 6.1 Add a smoke check that starts from a clean local state and confirms an order and all expected telemetry signals.
- [x] 6.2 Run every documented incident scenario, check expected panel behavior, and record observed limits and local resource guidance.
- [x] 6.3 Complete the README with architecture, setup, dashboard tour, troubleshooting, and the deferred Kubernetes roadmap item.
