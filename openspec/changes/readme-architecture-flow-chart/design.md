## Context

The README currently uses a text block to describe the order and telemetry paths. The approved preview is a two-lane chart: order processing above observability. It shows the Kafka analytics branch, RabbitMQ fulfillment path, telemetry backends, Prometheus scrape targets, and Grafana's read-only PostgreSQL access.

## Goals / Non-Goals

**Goals:**
- Make the architecture easy to scan in the README.
- Keep the image legible at common desktop and mobile widths.
- Retain an editable vector source and provide a broadly rendered image asset.
- Keep the existing prose that explains delivery guarantees.

**Non-Goals:**
- Change services, application behavior, APIs, or deployment configuration.
- Redesign the architecture or add components beyond those in the current system.

## Decisions

- Use the approved chart as the visual source of truth, with the order flow and observability flow separated into two panels.
- Embed a PNG in README for consistent rendering across Markdown viewers, and keep the SVG alongside it as the editable source.
- Use relative asset paths and descriptive alt text so the README works from the repository and remains accessible.
- Keep the existing paragraph on at-least-once delivery and duplicate safety immediately after the chart.

Alternatives considered: retain the text diagram (does not communicate the full flow clearly); use a Mermaid block (rendering varies across Markdown viewers and is not an image asset); embed only SVG (crisp and editable, but SVG display support varies among Markdown viewers).

## Risks / Trade-offs

- [PNG text may look soft when enlarged] → Export at 1800 pixels wide and retain the SVG source for future edits.
- [Diagram can drift from the running system] → Keep labels aligned with `compose.yaml` and the README's existing architecture description.

## Migration Plan

Add the final PNG and SVG under `docs/`, replace the README text diagram with the PNG and descriptive alt text, then confirm both relative paths resolve. Rollback by restoring the text block and removing the two image assets.

## Open Questions

None.
