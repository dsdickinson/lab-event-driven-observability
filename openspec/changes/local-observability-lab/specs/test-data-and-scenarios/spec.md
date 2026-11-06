## ADDED Requirements

### Requirement: Default test data
The project SHALL include a small generated fixture and a traffic generator that creates ongoing local order activity without an external data source.

#### Scenario: Default demo
- **WHEN** the default Compose project starts
- **THEN** valid orders are generated and relevant dashboards gain data within a documented warm-up period

### Requirement: Optional historical data import
The project SHALL offer a documented importer for a user-supplied Olist dataset and SHALL NOT require or bundle that dataset for default operation.

#### Scenario: User supplies dataset
- **WHEN** a user places the expected Olist files in the documented import location and runs the import command
- **THEN** representative records are validated and made available as inputs for new local traffic

### Requirement: Controlled incident scenarios
The project SHALL provide repeatable ways to create slow API responses, an unavailable API probe, fulfillment backlog, Kafka consumer lag, and failed fulfillment.

#### Scenario: Exercise a failure
- **WHEN** a user runs a documented incident scenario
- **THEN** the relevant telemetry changes in a predictable direction and the scenario can be returned to baseline

