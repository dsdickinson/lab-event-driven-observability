## ADDED Requirements

### Requirement: README architecture image
The README SHALL present the system architecture as an image chart that shows the complete order processing and observability flows represented by the current system.

#### Scenario: Reader follows order processing
- **WHEN** a reader views the architecture section
- **THEN** the chart shows generated traffic through the API, PostgreSQL outbox, publisher, Kafka, dispatcher, RabbitMQ, and fulfillment worker, including the worker's status update to PostgreSQL and Kafka's independent analytics consumer

#### Scenario: Reader follows observability
- **WHEN** a reader views the architecture section
- **THEN** the chart shows application telemetry through the OpenTelemetry Collector to Prometheus, Loki, and Tempo, infrastructure scrape targets to Prometheus, and Grafana access to telemetry stores and read-only PostgreSQL

#### Scenario: Image is accessible and portable
- **WHEN** the README is rendered in a Markdown viewer
- **THEN** the architecture image uses a repository-relative path and descriptive alternative text
