# Telemetry Gap Ledger

Date: 2026-03-16

Purpose:
- make `lab-llm` the accountability surface for telemetry quality
- turn `docs/successful_lab.md` into a working gap list
- record why the dashboard is not yet answering core operator questions
- define the upstream facts `model-runner` must provide or clarify

## How to use this file
Each gap is phrased in product terms, not schema terms.

Template:
- `Question`: what the operator is trying to answer
- `Expected answer`: what a useful dashboard should say
- `Current behavior`: what the dashboard says now
- `Telemetry gap`: what is missing, ambiguous, noisy, or wrong upstream
- `Dashboard gap`: what `lab-llm` still fails to interpret or present clearly
- `Fallback`: how the dashboard should behave until the gap is fixed
- `Upstream owner`: usually `model-runner`
- `Status`: `open`, `partial`, or `closed`

## Current audit summary
Relative to `docs/successful_lab.md`, the current dashboard is:
- **partially useful** for a narrow slice of session/turn inspection
- **not yet useful** for trustworthy diagnosis
- **not yet understandable** enough for a non-expert operator

The dominant failure modes are:
- the audited dashboard/API is lagging newer canonical telemetry truth
- model/load/runtime facts are still too incomplete or too raw on the rendered surface
- unknown vs noisy vs trustworthy signals are not clear enough
- performance plots exist without enough explanation context
- freshness and source-state cards still misstate or hide available evidence
- the UI still exposes telemetry quality problems more than it resolves them

## Audit notes
Latest direct audit inputs:
- screenshot: `frontend/artifacts/latest.png`
- screenshot history: `frontend/artifacts/history-2026-03-16T08-06-19-037Z.png`
- API captures:
  - `frontend/artifacts/api-status-20260316T080618Z.json`
  - `frontend/artifacts/api-sessions-20260316T080618Z.json`
  - `frontend/artifacts/api-session-detail-20260316T080618Z.json`
- upstream response and verification evidence:
  - `docs/coordination/inbox/response.md`
  - `docs/coordination/inbox/artifacts/hf-qwen35-9b-sess_d8f3abe025ee4201abab2d30fa06188f.jsonl`

The findings below are based on the rendered dashboard and those live artifacts, not on hypothetical UI issues.
Upstream-only improvements are recorded as `partial` unless the audited dashboard/API also reflects them.

## Model reality gaps
### GAP-001: What model actually loaded?
- `Question`: What model did the runtime actually load?
- `Expected answer`: A human-readable model identity, not just a filesystem path unless no better identity exists.
- `Current behavior`: In the newest audited screenshot and API captures, the operator still gets path-like identity on the main surface: session rows use `resolved_model_id`, the selected title is `/home/poop/ml/models/Qwen3.5-9B`, and no separate display-label/path fields appear. The sessions API at `frontend/artifacts/api-sessions-20260316T080618Z.json` still lists the newly verified finished session `sess_d8f3abe025ee4201abab2d30fa06188f` with only path-like `resolved_model_id`, even though the canonical verification artifact now carries `model_display_name: "Qwen3.5-9B"` plus explicit `model_path`.
- `Telemetry gap`: canonical runner telemetry is improved for the verified 2026-03-16 HF session, but the audited dashboard capture is still backed by older path-only projections/data for the operator surface.
- `Dashboard gap`: the dashboard still treats path-like identifiers as if they were normal model names.
- `Fallback`: show path only when no better identity exists, label it explicitly as a path, and avoid repeating it across multiple cards.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-015: The same path is repeated as session title, page title, and model value
- `Question`: What model loaded, without making the operator parse a filesystem path repeatedly?
- `Expected answer`: One clear primary model label, with filesystem path available separately when needed.
- `Current behavior`: `frontend/artifacts/latest.png` still shows `/home/poop/ml/models/Qwen3.5-9B` as the selected session title, page title, and model value. `frontend/artifacts/api-sessions-20260316T080618Z.json` still exposes only path-like `resolved_model_id` rows, including the newer verified finished session `sess_d8f3abe025ee4201abab2d30fa06188f`.
- `Telemetry gap`: upstream canonical events now separate `model_display_name` and `model_path` for the verified 2026-03-16 session, but the audited sessions/detail API still does not project those fields.
- `Dashboard gap`: the dashboard repeats the path in multiple “identity” positions instead of collapsing it into one labeled path field and one human-facing model label.
- `Fallback`: derive a short display name from the basename when only a path is available, and label the full path explicitly as `Model path`.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-002: Which runtime engine and attention path are actually active?
- `Question`: Which engine loaded the model, and what attention implementation is really active?
- `Expected answer`: Engine and attention backend are visible in a clear load summary.
- `Current behavior`: some load truth exists, but it is still mostly raw JSON and may be partial.
- `Telemetry gap`: upstream load reports are incomplete and may arrive incrementally.
- `Dashboard gap`: the dashboard does not clearly separate confirmed load facts from missing ones.
- `Fallback`: show explicit “unknown/not yet confirmed” states in summary cards.
- `Upstream owner`: shared, with truth from `model-runner`
- `Status`: `partial`

### GAP-016: Source/path status is missing even when the dashboard is live
- `Question`: Where is this dashboard getting its telemetry from right now?
- `Expected answer`: Source mode and source path should be visible whenever the dashboard is running.
- `Current behavior`: The screenshot still shows `Source Unavailable` and `Path Unavailable`. The newest status capture is `{ "ingestion": null, "note": "status endpoint unavailable on audited backend" }`, so the operator still cannot tell whether the source is genuinely unknown or merely not exposed by this backend version.
- `Telemetry gap`: the audited backend still does not expose inspectable source mode/path state through the status API.
- `Dashboard gap`: the page presents “Unavailable” rather than a more honest statement such as “status endpoint missing on this backend version.”
- `Fallback`: distinguish `dashboard cannot inspect source` from `source genuinely unknown`.
- `Upstream owner`: shared
- `Status`: `open`

### GAP-027: Freshness summary says `Latest event Not yet` even when events are present
- `Question`: Is telemetry live, stale, or broken?
- `Expected answer`: The summary should show the latest observed event time, or clearly say which evidence path is missing.
- `Current behavior`: `frontend/artifacts/latest.png` still shows `Latest event Not yet`, but `frontend/artifacts/api-session-detail-20260316T080618Z.json` includes `session.last_event_at: "2026-03-16T08:06:17.491Z"` and `latest_runtime.ts: "2026-03-16T08:06:17.488Z"` for the selected session.
- `Telemetry gap`: none required for the audited session; usable freshness timestamps are already present.
- `Dashboard gap`: the freshness card is not wired to available evidence, so it makes live telemetry look absent.
- `Fallback`: render the newest observed timestamp from session/detail data, or state explicitly that the freshness source is unavailable on this backend.
- `Upstream owner`: `lab-llm`
- `Status`: `open`

### GAP-003: Did the runtime silently change configuration?
- `Question`: Did dtype, quantization, context length, or attention silently differ from what was intended?
- `Expected answer`: The dashboard should surface confirmed runtime values and make mismatches obvious.
- `Current behavior`: The audited detail payload for the selected session `sess_c7acaf69b1cc451081d7038203fd9c1e` still shows one projected `context_length: 49152` in `load_report` and `inspect.load_truth`, with no requested-vs-confirmed split or mismatch hint. The verified upstream session `sess_d8f3abe025ee4201abab2d30fa06188f` now carries `payload.extension.runtime_truth.requested`, `confirmed`, and `mismatches`, including a confirmed `context_length: 262144` vs requested `49152`.
- `Telemetry gap`: canonical runner telemetry is improved for the verified 2026-03-16 HF session, but the audited dashboard/API still does not project the new runtime-truth split or mismatch evidence.
- `Dashboard gap`: there is no mismatch-oriented view yet.
- `Fallback`: never present requested config as runtime truth; show only confirmed facts and mark the rest unknown.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-017: Summary cards overclaim certainty when key fields are absent
- `Question`: Can an operator trust the summary without reading raw JSON?
- `Expected answer`: Summary cards should only state confirmed facts and should not imply a complete explanation when important fields are missing.
- `Current behavior`: The screenshot shows confident summaries for model/runtime while TTFT, stop reason, GPU util, KV util, source, and path are unavailable.
- `Telemetry gap`: some key upstream fields are absent.
- `Dashboard gap`: the page still reads like a complete dashboard rather than a partial truth surface with obvious holes.
- `Fallback`: add stronger “partial data” signaling at the card or section level when critical fields are missing.
- `Upstream owner`: `lab-llm`
- `Status`: `open`

## GPU and memory gaps
### GAP-004: What is the GPU doing right now?
- `Question`: Is the GPU compute-bound, memory-bound, idle, or blocked?
- `Expected answer`: A non-expert should see the relevant GPU state quickly.
- `Current behavior`: The audited screenshot still shows a `GPU util` card with `Unavailable` and no samples, while `frontend/artifacts/api-session-detail-20260316T080618Z.json` for the selected session still exposes only VRAM bytes. The verified upstream session `sess_d8f3abe025ee4201abab2d30fa06188f` now emits utilization, power, temperature, and explicit GPU `measurement_state` plus `diagnosis_state: "incomplete"`, but that richer truth is not visible on the audited operator surface.
- `Telemetry gap`: canonical runner telemetry is improved because GPU coverage and incompleteness are now explicit for the verified HF session, but the audited dashboard/API still does not expose enough of that truth to answer the operator question.
- `Dashboard gap`: there is no structured GPU state panel or interpretation language yet.
- `Fallback`: present only confirmed metrics and state clearly that diagnosis is incomplete.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-018: GPU card exists without enough signals to answer the GPU question
- `Question`: What is the GPU doing right now?
- `Expected answer`: Either a useful GPU state summary or a clear statement that the necessary signals are not present.
- `Current behavior`: The newest screenshot still shows a `GPU util` chart card with no samples and `GPU util Unavailable`, while `frontend/artifacts/api-session-detail-20260316T080618Z.json` only contains VRAM bytes for the selected live session. Upstream verified evidence for `sess_d8f3abe025ee4201abab2d30fa06188f` now includes `utilization_percent`, `power_usage_watts`, `temperature_celsius`, and explicit GPU diagnosis metadata, but the audited dashboard capture does not surface them.
- `Telemetry gap`: canonical runner telemetry now emits key GPU live signals for the verified HF session, but the audited dashboard/API is still backed by data or projections that expose only VRAM numbers to the operator.
- `Dashboard gap`: the chart panel occupies primary space without telling the operator what is missing or why it matters.
- `Fallback`: replace empty GPU charts with a compact “GPU telemetry incomplete” explanation until enough signals exist.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-005: Is memory behavior healthy?
- `Question`: Is memory fragmentation, offload, or cache pressure happening?
- `Expected answer`: The dashboard should let an operator infer whether memory behavior is normal or suspicious.
- `Current behavior`: runtime JSON may expose some allocator/cache data, but not in an understandable way.
- `Telemetry gap`: allocator/offload/swap signals are incomplete or absent upstream.
- `Dashboard gap`: there is no memory integrity summary layer yet.
- `Fallback`: preserve raw truth, but do not imply memory health when the signals are incomplete.
- `Upstream owner`: shared
- `Status`: `open`

## KV cache and throughput gaps
### GAP-006: Is KV cache limiting performance?
- `Question`: Is the cache underutilized, saturated, or thrashing?
- `Expected answer`: The dashboard should show cache size, usage trend, and whether cache pressure is a likely bottleneck.
- `Current behavior`: a KV utilization plot exists, but the surrounding explanation is not there.
- `Telemetry gap`: cache-level details like eviction/thrashing are incomplete upstream.
- `Dashboard gap`: the app charts cache numbers without enough operator interpretation.
- `Fallback`: say what is known, do not pretend to diagnose thrashing if the required signals do not exist.
- `Upstream owner`: shared
- `Status`: `open`

### GAP-019: KV cache panel overpromises while providing no usable signal
- `Question`: Is KV cache helping, limiting, or irrelevant here?
- `Expected answer`: A real cache signal or an explicit statement that cache telemetry is absent.
- `Current behavior`: The screenshot shows `KV cache util Unavailable` and “No samples for this metric yet” in a first-class chart slot.
- `Telemetry gap`: canonical telemetry for the verified session now emits an explicit unavailable state with `measurement_state: "unavailable"` and `unavailable_reason: "backend_does_not_report_kv_cache_runtime_usage"`, but `frontend/artifacts/api-session-detail-20260316T080618Z.json` still omits any KV cache object or reason for the audited session.
- `Dashboard gap`: the app still allocates premium UI space to a chart that cannot answer anything.
- `Fallback`: collapse missing-signal charts into a lower-emphasis telemetry-missing state instead of presenting them like working panels.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-007: Are tok/s numbers trustworthy?
- `Question`: Is generation speed actually good/bad, or is the metric noisy and misleading?
- `Expected answer`: The dashboard should either show a trustworthy tok/s value or clearly say the metric is noisy/unknown.
- `Current behavior`: The newest screenshot and detail capture still headline numeric `Tok/s` while `requests_in_flight` is `0`; throughput is rendered as a plain number with no trust or measurement-state context. Upstream verified evidence for `sess_d8f3abe025ee4201abab2d30fa06188f` now emits `measurement_state`, `trust_level`, `trust_reason`, and idle samples with no numeric tok/s, but the audited dashboard surface does not show those semantics.
- `Telemetry gap`: canonical HF throughput semantics improved in the verified 2026-03-16 session, but the audited dashboard capture still exposes the older numeric-only throughput shape.
- `Dashboard gap`: the UI still renders tok/s with more confidence than the source telemetry deserves, and it cannot yet present the newer trust semantics.
- `Fallback`: mark throughput as provisional/noisy for affected sources until verified; do not imply confidence.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-020: Tok/s is shown as the lead performance number even after the request has completed
- `Question`: What is happening right now, and is tok/s still a live indicator?
- `Expected answer`: The operator should know whether tok/s reflects active generation, completed-turn decay, or stale telemetry.
- `Current behavior`: The newest screenshot highlights `Tok/s 1.199873226785108` and a throughput chart while the newest detail capture simultaneously shows `requests_in_flight: 0` and `requests_completed_total: 2`.
- `Telemetry gap`: verified upstream telemetry no longer emits decaying idle tok/s for the new 2026-03-16 session, but the audited dashboard capture still relies on data/projections that do.
- `Dashboard gap`: the dashboard treats tok/s as the headline live metric even though the run may no longer be actively generating.
- `Fallback`: down-rank tok/s or mark it stale/non-live whenever `requests_in_flight` is zero and no active generation signal exists.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-008: Can the operator distinguish raw speed from effective speed?
- `Question`: Is the system fast at generation, or just hiding latency elsewhere?
- `Expected answer`: Raw generation rate and effective request speed should be clearly distinguished.
- `Current behavior`: The audited detail payload for `sess_c7acaf69b1cc451081d7038203fd9c1e` still exposes `tokens_generated_per_second` and `effective_tokens_per_second` with the same value, so the operator still gets one merged speed story. The verified upstream session `sess_d8f3abe025ee4201abab2d30fa06188f` now separates idle runtime throughput semantics from completed-turn raw vs effective speed, including `raw_completion_tokens_per_second: 28.016341890322057` and `effective_completion_tokens_per_second: 22.884639184657416`.
- `Telemetry gap`: canonical throughput truth is improved for the verified HF session, but the audited dashboard/API still does not project those separate speed semantics to the operator.
- `Dashboard gap`: the current summaries are still too metric-centric and not explanatory enough.
- `Fallback`: show missing effective-speed metrics as unknown instead of folding them into one “tok/s” idea.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-021: Raw and effective speed are still visually collapsed into one story
- `Question`: Is this speed number raw generation speed, effective request speed, or something else?
- `Expected answer`: Raw and effective speed should be clearly distinct or explicitly merged only when the dashboard can justify it.
- `Current behavior`: The newest detail capture still exposes both `tokens_generated_per_second` and `effective_tokens_per_second` with the same value, so the operator still gets one visually merged speed story. Upstream verified runtime samples for `sess_d8f3abe025ee4201abab2d30fa06188f` now omit fabricated `effective_tokens_per_second` and instead carry measurement basis/trust metadata, but that distinction is not visible in the audited dashboard surface.
- `Telemetry gap`: canonical upstream semantics are improved for the verified session, but the audited API contract still makes raw and effective speed look like the same thing.
- `Dashboard gap`: the UI does not teach the operator the difference, so even correct data is easy to misread.
- `Fallback`: label throughput cards more precisely or show a note when only one trustworthy speed story is available.
- `Upstream owner`: `lab-llm`
- `Status`: `partial`

## Latency and request flow gaps
### GAP-009: Where is latency accumulating?
- `Question`: Is latency coming from prefill, decode, queueing, or something unknown?
- `Expected answer`: The dashboard should help narrow the source of latency quickly.
- `Current behavior`: some turn-level timing may appear, but not as an interpretable latency story.
- `Telemetry gap`: upstream timing breakdowns are incomplete and inconsistent.
- `Dashboard gap`: there is no latency diagnosis surface yet.
- `Fallback`: expose timing fields separately and mark the diagnosis as incomplete.
- `Upstream owner`: shared
- `Status`: `open`

### GAP-022: Turn summary hides a very important latency fact by rendering it as unavailable
- `Question`: How long did the last request really take, and where is that shown?
- `Expected answer`: The last-turn summary should surface the most important timing fields that are actually available.
- `Current behavior`: The screenshot still shows `TTFT Unavailable` in the recent-turn strip for the selected audited session, even though latency is otherwise present. In the verified upstream session `sess_d8f3abe025ee4201abab2d30fa06188f`, `turn_finished` now carries `request_latency_seconds: 5.593271493911743`, `time_to_first_token_seconds: 1.0245094299316406`, and `decode_latency_seconds: 4.5687620639801025`, but the audited dashboard/API surface does not expose an equivalent richer turn summary yet.
- `Telemetry gap`: canonical turn telemetry is improved for the verified session, but the audited recent-turn projection still does not show TTFT or a clearer latency breakdown for the operator.
- `Dashboard gap`: the turn summary does not pivot to the strongest available timing signal when a preferred one is missing.
- `Fallback`: show available request/decode latency prominently even when TTFT is unavailable.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-010: Are requests queueing or batching?
- `Question`: Is the engine idle, queue-saturated, batch-limited, or stalled?
- `Expected answer`: The dashboard should clearly show request flow health.
- `Current behavior`: request flow is mostly absent from the current dashboard surface.
- `Telemetry gap`: queue and batch signals are weak or missing for many paths upstream.
- `Dashboard gap`: there is no request flow panel yet.
- `Fallback`: do not imply queueing/batching state unless the metrics are present.
- `Upstream owner`: shared
- `Status`: `open`

### GAP-023: Session state and request state do not reconcile clearly
- `Question`: Is this session actively generating right now, or merely still open?
- `Expected answer`: `running`, `idle`, `generating`, and `finished` should be distinguishable enough that request state makes sense.
- `Current behavior`: The screenshot shows `Status running` and `Live`, while the raw runtime shows `requests_in_flight: 0` and the only visible turn already finished.
- `Telemetry gap`: canonical telemetry for the verified session now separates lifecycle and activity with `activity_state` and `activity_state_reason`, but the audited session/detail API still exposes only `status` plus request counters.
- `Dashboard gap`: the dashboard conflates “process still alive” with “actively generating now.”
- `Fallback`: introduce an operator-facing derived activity state such as `idle` when the session is open but no request is in flight.
- `Upstream owner`: shared
- `Status`: `partial`

## Turn/debug gaps
### GAP-011: Can a non-expert understand the last turn quickly?
- `Question`: What happened on the last turn, how many tokens came out, and why did it stop?
- `Expected answer`: A clear plain-language summary with raw detail available if needed.
- `Current behavior`: recent turns are present, but the presentation is still too raw and metric-first.
- `Telemetry gap`: turn stop semantics may still be inconsistent upstream.
- `Dashboard gap`: the last-turn summary is not yet accessible enough for non-experts.
- `Fallback`: keep raw JSON accessible but move toward more readable summaries.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-024: The recent-turn strip is too compressed to be a useful explanation surface
- `Question`: What happened on the last turn?
- `Expected answer`: A non-expert should get outcome, duration, token count, and stop reason from one readable row or card.
- `Current behavior`: The screenshot shows `Turn 1`, `TTFT Unavailable`, and `Out 8192`, but no stop reason and no plain-language explanation of what 8192 means.
- `Telemetry gap`: canonical turn telemetry is improved for the verified session because `turn_finished` now carries `stop_reason` and `stop_reason_source`, but the audited session/detail API still does not project that richer explanation into the rendered turn strip.
- `Dashboard gap`: the turn surface is still too terse and too metric-fragmented.
- `Fallback`: prefer a richer last-turn summary card over a narrow metrics strip when upstream detail is partial.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-012: Can every panel be traced back to raw truth?
- `Question`: What raw data produced this state?
- `Expected answer`: Every important panel has a raw JSON/log/event escape hatch.
- `Current behavior`: projected inspect JSON is present in several places, which is good, but the newest audited detail capture only exposes `load_truth`, `generation_truth`, and `backend_extensions`; it does not expose the canonical raw event fields that now matter for model identity split or throughput trust semantics.
- `Telemetry gap`: none required for the principle itself.
- `Dashboard gap`: the app needs stronger “summary first, raw proof second” discipline across all panels.
- `Fallback`: keep raw JSON close to every summary view.
- `Upstream owner`: `lab-llm`
- `Status`: `partial`

### GAP-025: Logs currently duplicate timestamps and backend prefixes inside the rendered message
- `Question`: Can the operator read logs quickly without parsing duplicated formatting noise?
- `Expected answer`: The log surface should present source, timestamp, and message cleanly once.
- `Current behavior`: The screenshot still shows log rows like `backend 2026-03-16T06:17:26.487Z [backend] turn_finish ...`, duplicating source and timestamp inside the message body. In the verified upstream session `sess_d8f3abe025ee4201abab2d30fa06188f`, the canonical `log_recorded.payload.message` values are now clean strings like `turn_start id=1 messages=1 stream=True max_new_tokens=128` and `turn_finish id=1 elapsed_s=5.593 think_chars=417 answer_chars=0`, but the audited detail capture still exposes `logs: null`.
- `Telemetry gap`: canonical log message semantics are improved for the verified session, but the audited operator surface is still not showing those cleaner payloads.
- `Dashboard gap`: the dashboard either renders older preformatted log strings or cannot trace the rendered rows back to the captured API cleanly.
- `Fallback`: detect preformatted log messages and strip redundant prefixes at render time, or render only one canonical representation.
- `Upstream owner`: shared
- `Status`: `partial`

### GAP-026: Canonical telemetry fixes are not reaching the audited dashboard API
- `Question`: Did the newer upstream truth actually make it to the operator surface?
- `Expected answer`: When canonical telemetry adds model display/path split, throughput trust state, or GPU live signals, the session/detail API and inspect surface should expose them.
- `Current behavior`: The inbox verification artifact for `sess_d8f3abe025ee4201abab2d30fa06188f` includes `model_display_name`, `model_path`, activity state, KV measurement state, throughput `measurement_state`/`trust_level`, distinct raw vs effective turn throughput, richer turn latency fields, cleaned log messages, and GPU utilization/power/temperature. The newest audited frontend captures still expose path-only identity, numeric idle tok/s, VRAM-only GPU fields, no activity state, no KV measurement state, no richer turn timing fields, and no raw-event view of those canonical fields.
- `Telemetry gap`: none for the verified upstream session.
- `Dashboard gap`: `lab-llm` read models and API projections are still lagging the canonical event schema, so real upstream fixes do not reliably reach the operator surface.
- `Fallback`: label the audited backend as using an older projection and keep canonical raw-event evidence reachable until the API catches up.
- `Upstream owner`: `lab-llm`
- `Status`: `open`

## Session navigation gaps
### GAP-028: The session list is too ambiguous to help an operator pick the right run
- `Question`: Which session should I open to inspect the run I care about?
- `Expected answer`: The list should make runs distinguishable by human label plus a small amount of provenance such as status, freshness, ended time, or error state.
- `Current behavior`: In `frontend/artifacts/latest.png`, the left rail shows several nearly identical rows with the same truncated path-like model label and tiny `hf` plus `running` or `finished` badges. The newest sessions API already includes `started_at`, `ended_at`, `last_event_at`, and `has_errors` for each row, including both the selected long-running session `sess_c7acaf69b1cc451081d7038203fd9c1e` and the newer verified finished session `sess_d8f3abe025ee4201abab2d30fa06188f`, but the rendered list does not surface enough of that context to choose confidently.
- `Telemetry gap`: none required for a basic disambiguation pass; the sessions API already has enough timing and error metadata to improve the list materially.
- `Dashboard gap`: the session list hides too much row context, so the operator must click through multiple nearly identical entries to find the relevant run.
- `Fallback`: show a compact secondary line with freshness or ended time and retain a short stable identifier when labels collide.
- `Upstream owner`: `lab-llm`
- `Status`: `open`

## Synthesis and comparison gaps
### GAP-013: What is currently limiting performance?
- `Question`: What is the most likely bottleneck right now?
- `Expected answer`: The dashboard should at least narrow the diagnosis to compute, memory, KV cache, queueing, or unknown.
- `Current behavior`: the app is not yet capable of giving a credible diagnosis, even manually.
- `Telemetry gap`: multiple upstream signals are incomplete.
- `Dashboard gap`: there is no diagnosis-oriented synthesis layer yet.
- `Fallback`: explicitly say “cannot yet determine” and surface which signals are missing.
- `Upstream owner`: shared
- `Status`: `open`

### GAP-014: Did this configuration improve anything?
- `Question`: Did a change in backend/config/context/quantization improve performance?
- `Expected answer`: The app should support experiment comparison once the basics are trustworthy.
- `Current behavior`: comparison is effectively absent.
- `Telemetry gap`: experiment labeling and stable comparative signals are not yet mature enough upstream.
- `Dashboard gap`: comparison workflows are not started, which is acceptable until operational debugging is trustworthy.
- `Fallback`: defer comparison until single-run truth is reliable.
- `Upstream owner`: shared
- `Status`: `open`
