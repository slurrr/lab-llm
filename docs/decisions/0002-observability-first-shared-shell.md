# 0002 - Build an observability-first web product with room for chat later

Date: 2026-03-15

## Context
The immediate need is a useful observability surface:
- sessions
- throughput
- latency
- hardware
- cache behavior
- logs
- request truth

There is also a likely future need for browser chat on the same surface.

If chat drives the architecture too early, the observability product becomes vague.
If observability and chat are built as separate browser products, session semantics will drift.

## Decision
This repo will be observability-first in early phases.

The browser app should still be structured as a shared shell that can later host:
- `Observe`
- `Chat`

V1 only needs to implement the observability product area.

## Consequences
- Initial information architecture should prioritize monitoring, inspection, and comparison.
- Live session state, turn state, and inspect panels should be first-class concepts.
- Future chat should fit into the same navigation and session model rather than a separate app.
