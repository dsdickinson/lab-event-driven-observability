## Context

The repository has no application code. The first release is a local, job-portfolio observability lab: a believable order workflow, two brokers with different roles, and dashboards built from its real telemetry. Docker Compose is the deployment target. All runtime dependencies stay on the Compose network; downloading images and the optional Olist dataset is a setup action, not a runtime dependency.

## Goals / Non-Goals

**Goals:**

- One documented Compose startup path that yields traffic and populated Grafana dashboards.
- A traceable order journey across HTTP, PostgreSQL, Kafka, RabbitMQ, and workers.
- Repeatable healthy and failing scenarios with measurable dashboard changes.
- Readable, version-controlled service configuration, dashboard JSON, and verification commands that an interviewer can inspect.

**Non-Goals:**

- Kubernetes in this change; it is a later addition.
- Production high availability, multi-node brokers, secrets management, or internet-facing deployment.
- A customer-facing commerce product, payments, or use of real personal data.
- Claiming that local synthetic load proves production scale.

## Decisions

### Application and data

Use small Python services with a shared data contract: Order API, outbox publisher, Kafka-to-RabbitMQ dispatcher, fulfillment worker, and traffic generator. Python keeps the first version approachable while still requiring explicit instrumentation and asynchronous context propagation. A single service with background threads would use fewer containers but would hide service boundaries and broker behavior. PostgreSQL holds orders, outbox records, and idempotency records. The built-in fixture uses invented data; an optional importer reads a user-supplied Olist download without committing that dataset to the repository.

### Messaging and reliability

The Order API commits an order and outbox record in one PostgreSQL transaction. The publisher sends `order.placed` to Kafka and marks the outbox record published only after broker acknowledgement. The dispatcher consumes that event and publishes a fulfillment command to RabbitMQ with publisher confirmation, then commits the Kafka offset. The worker acknowledges RabbitMQ only after persisting the result. All consumers identify work by stable order/event IDs and tolerate duplicate delivery. This follows the agreed Kafka-first flow and avoids a direct API publish to both brokers. It is at-least-once delivery, not a claim of end-to-end exactly-once behavior.

Kafka topics represent retained facts that analytics can replay; RabbitMQ queues represent fulfillment work and retry/dead-letter behavior. A small analytics consumer computes a live order count or revenue metric from Kafka events so Kafka is exercised beyond merely forwarding to RabbitMQ. Keep topic and queue creation deterministic on startup.

### Telemetry routing

Application services emit OTLP metrics, structured logs, and traces to the OpenTelemetry Collector. The Collector exposes application metrics for Prometheus to scrape, sends logs to Loki's OTLP endpoint, and sends traces to Tempo. Prometheus also scrapes its own and Collector health metrics, RabbitMQ's built-in Prometheus endpoint, a Kafka metrics exporter, and Blackbox Exporter probes against the local Order API. Grafana provisions Prometheus, Loki, and Tempo data sources. Propagate trace context in Kafka headers and RabbitMQ message headers, and include trace IDs in logs. Prefer low-cardinality labels; order IDs belong in logs and traces, not metric labels.

### Dashboards and exercises

Provision version-controlled dashboards for: service/API health and RED metrics; order flow and outbox age; RabbitMQ depth, processing, retries, and dead letters; Kafka production rate and consumer lag; and observability pipeline health, including scrape targets, Collector failures, Loki/Tempo ingest, and Blackbox probe results. Add PostgreSQL as a read-only Grafana data source and include SQL panels for order counts, status breakdown, and fulfillment latency or recent failures. Use PromQL for operational time-series metrics and SQL for business records, with clear panel labels showing the source. Provide links from metric panels to relevant logs and traces where identifiers permit. Provide documented scenarios for baseline traffic, slow requests, paused fulfillment, dispatcher or analytics lag, failed fulfillment, and unavailable API. Each scenario states the expected panel changes and an investigation path.

### Local operations

Pin image versions during implementation, use named volumes for state, health checks for required dependencies, and a documented reset path. Default startup uses only local services and the generated fixture. A short verification command checks service health and that each signal reaches its intended backend. Keep optional dataset import and heavier load behind explicit commands so the default demo fits a development machine.

## Risks / Trade-offs

- **Two brokers increase resource use and operational complexity** → Give each a distinct role, keep one-node local deployments, and document minimum machine resources after measurement.
- **Publish acknowledgement can be followed by a crash before offset or outbox state is saved** → Use stable IDs and idempotent processing; test duplicate delivery.
- **Cross-broker traces can break at asynchronous boundaries** → Explicitly inject and extract trace context in message headers and verify an order trace spans both brokers.
- **A historical dataset does not produce live incidents** → Generate new traffic from fixtures and provide controlled failure modes.
- **Olist has a noncommercial share-alike license** → Do not bundle it; keep the importer optional and document source and license.
- **Metrics can overload a laptop or become expensive to query** → Limit scrape frequency and label cardinality; use bounded default traffic and retention.

## Migration Plan

This is a new repository implementation, so there is no existing runtime to migrate. Build in slices: Compose infrastructure, order flow, instrumentation, dashboards, scenarios, then optional dataset import. Rollback of a failed local build is stopping Compose and, only when intentionally resetting test data, removing named volumes through the documented reset command.

## Open Questions

- Exact container image versions and Python libraries will be selected during implementation and pinned in the repository.
- Local memory and disk guidance will be measured after the stack runs rather than guessed in the proposal.
