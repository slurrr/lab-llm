# AGENTS

## Purpose
This repo is the browser-side observability and control surface for a local LLM lab.

Primary goals:
- ingest telemetry from the runner repo
- make runtime behavior visible and comparable
- provide a clean browser product for observability first
- preserve a path to future same-surface browser chat

## Scope
- Keep this repo focused on ingestion, read models, APIs, and UI.
- Do not duplicate model execution or backend runtime code here.
- Prefer session- and turn-aware product concepts over generic metrics-only views.
- Keep the repo easy to navigate.

## Conventions
- Treat the runner repo as the telemetry producer.
- Consume telemetry through external interfaces; do not rely on runner internal imports as the primary path.
- Prefer clear separation between:
  - decisions in `docs/decisions/`
  - implementation specs in `docs/specs/`
  - dashboard architecture notes in `docs/dashboard_repo_architecture.md`
- Make unavailable metrics explicit in UI and API design.
- Favor practical, local-first development over heavy infrastructure.

## Current Direction
- Observability is the first product area.
- Chat may later live in the same browser shell, but should not drive v1 scope.
- Prometheus/Grafana compatibility is useful, but the product should not reduce itself to generic scrape dashboards.

## Usage
Use this repo for:
- dashboard architecture
- telemetry ingestion
- service/API design
- browser UI implementation

Do not use this repo for:
- model loading
- backend execution
- engine-specific runtime experimentation
