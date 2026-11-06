# Local observability project notes

## Current direction

- Build the application and observability stack from scratch for local use with Docker Compose.
- Include Grafana, Prometheus, Blackbox Exporter, an OpenTelemetry Collector, Loki, Tempo, RabbitMQ, Kafka, and PostgreSQL.
- Use PostgreSQL for orders and an outbox. Publish order events to Kafka, then have a consumer create RabbitMQ fulfillment tasks.
- Start with a small generated fixture and live traffic. Add an optional importer for the Olist e-commerce dataset later.
- Build Grafana dashboards and panels for application health, order processing, message backlogs, and telemetry pipeline health.

## Later addition

- Add Kubernetes deployment and cluster monitoring after the Docker Compose project is working. Kubernetes is outside the initial scope.
