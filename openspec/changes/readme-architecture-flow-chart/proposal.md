## Why

The README's text diagram names the main services but does not clearly show the complete order lifecycle, its independent analytics branch, or how operational signals reach Grafana. A visual chart will make the system easier to understand at a glance.

## What Changes

- Replace the README's text architecture block with a linked, accessible image chart.
- Show the order and fulfillment path, the independent analytics consumer, telemetry storage, and Grafana data sources.
- Preserve the explanatory text about delivery guarantees and duplicate safety.

## Capabilities

### New Capabilities
- `readme-architecture-chart`: A complete visual overview of the local observability demo's process and telemetry flows.

### Modified Capabilities

## Impact

- `README.md` architecture section.
- A new SVG architecture diagram asset stored with the repository documentation.
- No application behavior, service APIs, or runtime dependencies change.
