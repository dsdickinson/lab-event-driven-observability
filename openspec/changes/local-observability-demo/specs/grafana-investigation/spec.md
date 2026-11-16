## ADDED Requirements

### Requirement: Provisioned dashboards
Grafana SHALL provision Prometheus, Loki, Tempo, and read-only PostgreSQL data sources and version-controlled dashboards for service health, order flow, RabbitMQ, Kafka, and telemetry pipeline health.

#### Scenario: New Grafana instance
- **WHEN** Grafana starts with an empty data volume
- **THEN** the expected data sources and dashboards appear without manual UI setup

### Requirement: Actionable panels
Dashboards SHALL include labeled PromQL panels for request rate, errors, latency, outbox backlog or age, RabbitMQ depth and failures, Kafka throughput and lag, probe results, and telemetry pipeline health. They SHALL include SQL panels for order counts, status breakdown, and fulfillment latency or recent failures from PostgreSQL.

#### Scenario: Fulfillment paused
- **WHEN** fulfillment is paused while orders continue
- **THEN** a user can see increasing task backlog and identify the affected workflow from dashboard panels

#### Scenario: Compare operational and business data
- **WHEN** a user opens the order dashboard during live traffic
- **THEN** they can compare Prometheus metrics with SQL results from persisted orders and identify the data source used by each panel

### Requirement: Cross-signal investigation
The project SHALL document an incident path from an alerting metric or probe panel to related logs and traces using Grafana links or clear query instructions.

#### Scenario: Investigate failed order
- **WHEN** a generated order fails fulfillment
- **THEN** a user can locate its failure log and associated distributed trace from the dashboard investigation path

