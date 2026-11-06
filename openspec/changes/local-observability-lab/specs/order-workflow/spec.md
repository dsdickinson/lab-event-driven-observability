## ADDED Requirements

### Requirement: Durable order event
The Order API SHALL save each accepted order and its pending event in one PostgreSQL transaction; an outbox publisher SHALL publish the event to Kafka and record success only after broker acknowledgement.

#### Scenario: Order accepted
- **WHEN** a valid order is submitted
- **THEN** the API returns a stable order ID and the order and pending event are persisted together

#### Scenario: Kafka is unavailable
- **WHEN** an order is accepted while Kafka cannot acknowledge publication
- **THEN** the order remains persisted and its event remains pending for retry

### Requirement: Kafka-to-RabbitMQ dispatch
The dispatcher SHALL turn each `order.placed` Kafka event into a RabbitMQ fulfillment task and commit its Kafka offset only after RabbitMQ confirms publication.

#### Scenario: Dispatch succeeds
- **WHEN** the dispatcher receives an order event
- **THEN** a fulfillment task with the stable event and order IDs is available to a worker

### Requirement: Duplicate-safe fulfillment
The fulfillment worker SHALL persist a terminal or retryable outcome before acknowledging its RabbitMQ task and SHALL avoid applying the same task twice.

#### Scenario: Duplicate delivery
- **WHEN** the same fulfillment task is delivered more than once
- **THEN** the order receives one fulfillment transition and duplicate deliveries do not create extra work results

#### Scenario: Fulfillment fails
- **WHEN** a task encounters a configured transient failure
- **THEN** it is retried according to a bounded policy and becomes visible as failed or dead-lettered when retries are exhausted

### Requirement: Kafka analytics consumer
An independent consumer SHALL process order events from Kafka and expose an observable aggregate and consumer lag.

#### Scenario: Consumer resumes
- **WHEN** analytics consumption pauses and later resumes
- **THEN** lag grows while paused and falls as retained events are processed

