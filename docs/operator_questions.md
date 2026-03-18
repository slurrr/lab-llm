# Operator Questions

These are the questions the dashboard must answer before it is considered useful.

The review surface is whether these questions are answerable quickly and honestly, not whether every panel looks complete.

## Core questions
- What model/backend actually loaded?
- Is telemetry live, stale, or broken?
- What is happening right now: loading, generating, finished, or errored?
- How fast is it going, and how trustworthy is that speed number?
- What is the likely bottleneck: compute, memory/cache, queueing, or unknown?
- What output did the last turn produce, and why did it stop?
- When I need proof, where is the raw JSON?

## Review rule
Every meaningful dashboard slice should improve at least one of these questions.

If a change does not improve a question directly, it should either:
- reduce ambiguity about a question, or
- improve the raw-debug path needed to validate an answer.
