## ADDED Requirements

### Requirement: Local startup
The project SHALL start the application, brokers, data store, and observability stack with a documented Docker Compose command and no cloud service dependency at runtime.

#### Scenario: Fresh local start
- **WHEN** a user follows the setup instructions on a machine with Docker Compose and downloaded images
- **THEN** all required services become healthy and Grafana exposes provisioned data sources and dashboards

### Requirement: Repeatable lifecycle
The project SHALL document how to stop, restart, and intentionally reset local state.

#### Scenario: Restart with persisted state
- **WHEN** a user stops and restarts the Compose project without a reset
- **THEN** stored orders and observability data remain available through named volumes

