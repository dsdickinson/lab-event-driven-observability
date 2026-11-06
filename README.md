# Local Observability Lab

A Docker Compose order system built from scratch to practice operating Grafana, Prometheus, Blackbox Exporter, OpenTelemetry Collector, Loki, Tempo, Kafka, RabbitMQ, and PostgreSQL. The default generated traffic creates real requests, events, tasks, metrics, logs, and traces. Five version-controlled Grafana dashboards include both **PromQL** operational panels and **SQL** order-data panels.

## Architecture

```text
traffic -> Order API -> PostgreSQL orders + outbox
                            |
                            v
                     outbox publisher -> Kafka orders.placed
                                           |             |
                                           v             v
                                      dispatcher     analytics
                                           |
                                           v
                                      RabbitMQ fulfillment
                                           |
                                           v
                                     fulfillment worker -> PostgreSQL

application OTLP -> OpenTelemetry Collector -> Prometheus / Loki / Tempo
RabbitMQ, Kafka exporter, Blackbox probe -> Prometheus
Grafana -> Prometheus, Loki, Tempo, read-only PostgreSQL
```

The order and its outbox event commit together. Publishing and delivery are **at least once**; stable event IDs and a `processed_events` table make fulfillment duplicate-safe. The Kafka dispatcher waits for RabbitMQ publisher confirmation before committing its Kafka offset. Kafka retains order facts; RabbitMQ carries fulfillment tasks. The analytics consumer reads Kafka independently.

## Run locally

Requirements: Docker Desktop or Docker Engine with Compose v2, free host ports 3000, 8000, 9090, 3100, 3200, 4318, 15672, and 55432. Allocate at least 6 GB of memory to Docker. A baseline run used about 2.4 GiB across containers, but Kafka, Tempo, and rebuilds need headroom. Images are downloaded at first start. No cloud service is used after setup.

```bash
docker compose up -d --build
docker compose ps
docker compose run --rm api python -m app.smoke
```

Open [Grafana](http://localhost:3000) with `admin` / `admin`. The RabbitMQ management UI is at [localhost:15672](http://localhost:15672) with `lab` / `lab`. Prometheus is at [localhost:9090](http://localhost:9090), and the Order API docs are at [localhost:8000/docs](http://localhost:8000/docs). These credentials and HTTP ports are for local development only.

The traffic generator creates about one order every three seconds. To change the rate, set `TRAFFIC_INTERVAL_SECONDS` before starting Compose. Stop without deleting data with `docker compose stop`. Restart with `docker compose up -d`. **Intentional full reset**, including orders and telemetry history: `docker compose down -v`.

## Dashboard tour

| Dashboard | Main questions | Query language |
| --- | --- | --- |
| 01 Service and API Health | Are orders arriving? Are requests slow or failing? Is the API reachable? | PromQL |
| 02 Order Flow and SQL | How many orders are pending or fulfilled? Is outbox publication stuck? | PromQL and PostgreSQL SQL |
| 03 RabbitMQ Fulfillment | Is the worker keeping up? Are tasks failing or dead-lettered? | PromQL |
| 04 Kafka Events | Are events published? Are either consumer groups falling behind? | PromQL |
| 05 Telemetry Pipeline | Are scrape targets, the Collector, and probes healthy? | PromQL |

Grafana's **Explore** view connects the same four data sources. An order creation response includes `order_id` and `trace_id`. Search Loki for the order ID, then open the trace ID in Tempo. The API log body also includes both IDs. For an interview, use a SQL panel to show persisted order status, then a PromQL panel to show operational rate or lag; SQL queries PostgreSQL records, while PromQL queries Prometheus time series.

## Incident exercises

Run one scenario at a time and use `baseline` to restore services. Allow 15–30 seconds for scrapes and dashboard refreshes.

```bash
python3 scripts/scenario.py fulfillment-backlog
python3 scripts/scenario.py baseline
```

| Scenario | Command argument | Expected evidence |
| --- | --- | --- |
| Slow API | `slow-api` | p95 API latency rises; probe duration may rise |
| API unavailable | `api-down` | `probe_success` falls to 0; traffic logs show failures |
| Fulfillment backlog | `fulfillment-backlog` | RabbitMQ ready tasks rise while Kafka and API continue |
| Kafka consumer lag | `kafka-lag` | `order-analytics` consumer lag rises |
| Failed fulfillment | `failed-fulfillment` | failure counter and `fulfillment.dead` queue rise; orders remain placed |

For a failed order, use the SQL recent-orders table to identify the order, search Loki for `order_id=<id>`, and use the log's `trace_id` to inspect its path through the services in Tempo. A worker stopped for backlog is a service interruption; the baseline command restarts it and clears the scenario's dead-letter queue.

## Optional Olist data

Default setup uses four invented products. For more variety, download the [Olist Brazilian e-commerce dataset](https://www.kaggle.com/olistbr/brazilian-ecommerce/home/) yourself and put `olist_products_dataset.csv` and `olist_order_items_dataset.csv` under `data/olist/`. Then run:

```bash
docker compose --profile tools run --rm olist-import
```

The importer loads up to 500 product IDs, categories, and first observed prices. It does **not** import customer information or historical orders. The live generator refreshes its product list within a minute and creates new orders from those products. Olist publishes the dataset under **CC BY-NC-SA 4.0**; it is not bundled with this repository.

## Verification and troubleshooting

`docker compose run --rm api python -m app.smoke` creates one order and checks fulfillment, the outbox, analytics, Prometheus metrics, a Blackbox probe, Loki logs, and a Tempo trace. `docker compose run --rm api python -m unittest discover -s tests` checks the importer. `docker compose logs -f api outbox dispatcher worker analytics otel-collector` follows the main pipeline. `docker compose config --quiet` validates Compose syntax.

If a dashboard panel is empty, check the Prometheus targets page first, then inspect the corresponding service logs. PostgreSQL is exposed on host port **55432** because port 5432 is commonly in use locally. All other service connections use Compose names and their internal ports.

This is a single-node local lab. It exercises failure symptoms and investigation paths, but it does not demonstrate high availability or production scale. Kubernetes deployment and cluster monitoring are reserved for a later addition.
