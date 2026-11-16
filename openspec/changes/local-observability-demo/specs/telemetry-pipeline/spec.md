## ADDED Requirements

### Requirement: Three-signal application telemetry
Application services SHALL emit metrics, structured logs, and distributed traces through the OpenTelemetry Collector to Prometheus, Loki, and Tempo respectively.

#### Scenario: Trace an order
- **WHEN** an order travels from API through Kafka, RabbitMQ, and fulfillment
- **THEN** the trace contains spans across the asynchronous boundaries and related logs contain a trace identifier

### Requirement: Infrastructure metrics
Prometheus SHALL scrape RabbitMQ metrics, Kafka broker or exporter metrics including consumer lag, and telemetry component health metrics.

#### Scenario: Broker backlog
- **WHEN** a RabbitMQ worker or Kafka consumer is paused under live traffic
- **THEN** Prometheus records a corresponding queue-depth or consumer-lag increase

### Requirement: Local availability probe
Blackbox Exporter SHALL probe at least one Order API HTTP endpoint through the Compose network and Prometheus SHALL record probe success and duration.

#### Scenario: API unavailable
- **WHEN** the probed API endpoint becomes unavailable
- **THEN** probe success drops and the failed target is identifiable in Grafana

### Requirement: Bounded telemetry
The default configuration SHALL use bounded retention and traffic and SHALL exclude per-order identifiers from metric labels.

#### Scenario: Multiple orders
- **WHEN** many distinct orders are generated
- **THEN** metrics can aggregate by service or operation without creating a series per order ID

