# 0003 - The dashboard repo owns the telemetry gap ledger

Date: 2026-03-15

## Context
This repo cannot become useful by polishing around weak or incomplete telemetry.

The runner repo emits telemetry, but the dashboard repo is where usability failures become obvious:
- duplicated or misleading labels
- unknown values shown as if they were facts
- noisy or untrustworthy metrics
- missing model/load/runtime truth
- views that fail to answer operator questions

If gap ownership stays split or informal, the dashboard will drift into generic UI work while telemetry truth problems remain unresolved.

## Decision
`lab-llm` owns the telemetry gap ledger.

That means:
- this repo records the operator questions the product must answer
- this repo records the telemetry gaps preventing those answers
- this repo defines the required upstream contract improvements
- `model-runner` is accountable to that ledger for telemetry truth and completeness

The runner repo still owns telemetry implementation.
This repo owns the product-facing definition of what is missing and why it matters.

## Consequences
- Dashboard work should be driven by question-answering gaps, not generic UI iteration.
- Every important dashboard slice should tie back to one or more operator questions.
- Telemetry issues found here should be written as upstream contract gaps rather than silently worked around.
- Raw JSON/debug surfaces remain important, but they are not the acceptance surface for usefulness.
