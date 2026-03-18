import { useEffect, useMemo, useState } from "preact/hooks";

import { MetricChart } from "./chart";
import type { IngestionStatus, SessionDetail, SessionSummary, SseEnvelope, TurnSummary, LogRecord, RuntimeSample } from "./types";

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function pretty(value: unknown): string {
  return JSON.stringify(value ?? "Unavailable", null, 2);
}

function readPreferredSessionId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  const params = new URL(window.location.href).searchParams;
  return params.get("session");
}

function writePreferredSessionId(sessionId: string): void {
  if (typeof window === "undefined") {
    return;
  }
  const url = new URL(window.location.href);
  url.searchParams.set("session", sessionId);
  window.history.replaceState({}, "", url);
}

export function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(() => readPreferredSessionId());
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ingestion, setIngestion] = useState<IngestionStatus | null>(null);

  async function refreshSessions() {
    const payload = await fetchJson<{ sessions: SessionSummary[] }>("/api/sessions");
    setSessions(payload.sessions);
    setSelectedSessionId((current) => {
      const available = new Set(payload.sessions.map((session) => session.session_id));
      const preferred = readPreferredSessionId();
      if (current && available.has(current)) {
        return current;
      }
      if (preferred && available.has(preferred)) {
        return preferred;
      }
      return payload.sessions[0]?.session_id ?? null;
    });
  }

  async function refreshDetail(sessionId: string) {
    const payload = await fetchJson<SessionDetail>(`/api/sessions/${sessionId}`);
    setDetail(payload);
  }

  useEffect(() => {
    refreshSessions().catch((err: Error) => setError(err.message));
    fetchJson<{ ingestion: IngestionStatus | null }>("/api/status")
      .then((payload) => setIngestion(payload.ingestion))
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedSessionId) {
      return;
    }
    refreshDetail(selectedSessionId).catch((err: Error) => setError(err.message));
  }, [selectedSessionId]);

  useEffect(() => {
    const source = new EventSource("/api/events");
    source.onmessage = () => {};
    const applyEnvelope = (eventType: string, envelope: SseEnvelope) => {
      setIngestion((current) =>
        current
          ? {
              ...current,
              connected: true,
              last_event_ts: envelope.ts,
              last_event_id: envelope.event_id,
            }
          : current
      );

      setSessions((current) => {
        const next = [...current];
        const index = next.findIndex((session) => session.session_id === envelope.session_id);
        if (index === -1) {
          next.unshift({
            session_id: envelope.session_id,
            status: eventType === "session_finished" ? String(envelope.payload.status ?? "finished") : eventType === "error_reported" ? "error" : "running",
            backend_name: envelope.backend_name,
            resolved_model_id: envelope.resolved_model_id,
            started_at: (envelope.payload.started_at as string | undefined) ?? null,
            ended_at: (envelope.payload.ended_at as string | undefined) ?? null,
            last_event_at: envelope.ts,
            has_errors: eventType === "error_reported",
          });
          return next;
        }
        const existing = next[index];
        next[index] = {
          ...existing,
          backend_name: envelope.backend_name ?? existing.backend_name,
          resolved_model_id: envelope.resolved_model_id ?? existing.resolved_model_id,
          last_event_at: envelope.ts,
          status:
            eventType === "session_finished"
              ? String(envelope.payload.status ?? "finished")
              : eventType === "error_reported"
                ? "error"
                : existing.status,
          ended_at:
            eventType === "session_finished"
              ? (envelope.payload.ended_at as string | undefined) ?? existing.ended_at
              : existing.ended_at,
          has_errors: existing.has_errors || eventType === "error_reported",
        };
        next.sort((a, b) => (b.last_event_at ?? "").localeCompare(a.last_event_at ?? ""));
        return next;
      });

      if (selectedSessionId !== envelope.session_id) {
        return;
      }

      setDetail((current) => {
        if (!current || current.session.session_id !== envelope.session_id) {
          return current;
        }
        const next: SessionDetail = {
          ...current,
          session: {
            ...current.session,
            last_event_at: envelope.ts,
          },
        };
        if (eventType === "load_reported") {
          next.load_report = { ...(current.load_report ?? {}), ...envelope.payload };
          next.inspect = { ...current.inspect, load_truth: next.load_report };
        } else if (eventType === "runtime_sample") {
          const sample = envelope.payload as unknown as RuntimeSample;
          next.latest_runtime = sample;
          next.runtime_history = [...current.runtime_history, sample].slice(-180);
        } else if (eventType === "turn_finished") {
          const turn = envelope.payload as unknown as TurnSummary;
          next.recent_turns = [turn, ...current.recent_turns.filter((item) => item.turn_id !== turn.turn_id)].slice(0, 20);
          next.inspect = { ...current.inspect, generation_truth: turn.knobs ?? current.inspect.generation_truth };
        } else if (eventType === "log_recorded") {
          const log = envelope.payload as unknown as LogRecord;
          next.recent_logs = [...current.recent_logs, log].slice(-200);
        } else if (eventType === "error_reported") {
          next.session = { ...next.session, status: "error", has_errors: true };
        } else if (eventType === "session_finished") {
          next.session = {
            ...next.session,
            status: String(envelope.payload.status ?? "finished"),
            ended_at: (envelope.payload.ended_at as string | undefined) ?? next.session.ended_at,
          };
        } else if (eventType === "session_started") {
          next.session = {
            ...next.session,
            status: String(envelope.payload.status ?? "running"),
            started_at: (envelope.payload.started_at as string | undefined) ?? next.session.started_at,
          };
        }
        return next;
      });
    };

    const bind = (eventType: string) => {
      source.addEventListener(eventType, (evt) => {
        try {
          const envelope = JSON.parse((evt as MessageEvent<string>).data) as SseEnvelope;
          applyEnvelope(eventType, envelope);
        } catch (err) {
          setError("Failed to parse live event.");
        }
      });
    };

    bind("runtime_sample");
    bind("turn_finished");
    bind("session_started");
    bind("session_finished");
    bind("log_recorded");
    bind("error_reported");
    bind("load_reported");
    source.addEventListener("connected", () => {
      setError(null);
      setIngestion((current) => (current ? { ...current, connected: true } : current));
    });
    source.onerror = () => setError("Live event stream disconnected.");
    return () => {
      source.close();
    };
  }, [selectedSessionId]);

  const selectedSession = useMemo(
    () => sessions.find((session) => session.session_id === selectedSessionId) ?? null,
    [selectedSessionId, sessions]
  );

  useEffect(() => {
    if (selectedSessionId) {
      writePreferredSessionId(selectedSessionId);
    }
  }, [selectedSessionId]);

  const latestTurn = detail?.recent_turns[0];
  const loadSummary = detail?.load_report;

  return (
    <div class="shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">Observe</p>
          <h1>lab-llm</h1>
          <p class="subtitle">Realtime local LLM observability with a future path to the same-shell chat UI.</p>
        </div>
        <div class="chip-row">
          <span class="chip">Preact</span>
          <span class="chip">uPlot</span>
          <span class="chip chip-muted">SSE live feed</span>
        </div>
      </header>

      <main class="layout">
        <section class="panel sidebar">
          <div class="panel-head">
            <h2>Sessions</h2>
            <button type="button" onClick={() => refreshSessions().catch((err: Error) => setError(err.message))}>
              Refresh
            </button>
          </div>
          <div class="session-list">
            {sessions.length === 0 ? <p class="empty-state">No sessions loaded yet.</p> : null}
            {sessions.map((session) => (
              <button
                key={session.session_id}
                type="button"
                class={`session-item ${session.session_id === selectedSessionId ? "selected" : ""}`}
                onClick={() => setSelectedSessionId(session.session_id)}
              >
                <span class="session-title">{session.resolved_model_id ?? session.session_id}</span>
                <span class="session-meta">
                  {session.backend_name ?? "unknown"} · {session.status}
                </span>
              </button>
            ))}
          </div>
        </section>

        <section class="panel detail">
          <div class="panel-head">
            <div>
              <h2>{selectedSession?.resolved_model_id ?? "Session detail"}</h2>
              <p class="muted">{selectedSession?.session_id ?? "No session selected"}</p>
            </div>
            {error ? <p class="status-error">{error}</p> : <p class="status-live">Live</p>}
          </div>

          <section class="source-strip">
            <div class="source-item">
              <span class="label">Source</span>
              <strong>{ingestion ? `${ingestion.mode} · ${ingestion.connected ? "connected" : "waiting"}` : "Unavailable"}</strong>
            </div>
            <div class="source-item source-path">
              <span class="label">Path</span>
              <strong>{ingestion?.source ?? "Unavailable"}</strong>
            </div>
            <div class="source-item">
              <span class="label">Last event</span>
              <strong>{ingestion?.last_event_ts ?? "None yet"}</strong>
            </div>
            <div class="source-item">
              <span class="label">Parse errors</span>
              <strong>{ingestion?.parse_error_count ?? 0}</strong>
            </div>
          </section>

          {!detail ? (
            <div class="empty-state">Select a session to inspect it.</div>
          ) : (
            <>
              <section class="metric-grid">
                <article class="metric-card">
                  <h3>Status</h3>
                  <p>{detail.session.status}</p>
                </article>
                <article class="metric-card">
                  <h3>Backend</h3>
                  <p>{detail.session.backend_name ?? "Unavailable"}</p>
                </article>
                <article class="metric-card">
                  <h3>Model</h3>
                  <p>{detail.session.resolved_model_id ?? "Unavailable"}</p>
                </article>
                <article class="metric-card">
                  <h3>Tok/s</h3>
                  <p>{detail.latest_runtime?.throughput?.tokens_generated_per_second ?? "Unavailable"}</p>
                </article>
              </section>

              <section class="summary-grid">
                <article class="subpanel">
                  <h3>Model summary</h3>
                  <dl class="summary-list">
                    <div><dt>Engine</dt><dd>{String(loadSummary?.engine_name ?? "Unavailable")}</dd></div>
                    <div><dt>Dtype</dt><dd>{String(loadSummary?.model_dtype ?? "Unavailable")}</dd></div>
                    <div><dt>Context</dt><dd>{String(loadSummary?.context_length ?? "Unavailable")}</dd></div>
                    <div><dt>Quantization</dt><dd>{String(loadSummary?.quantization_type ?? "Unavailable")}</dd></div>
                  </dl>
                </article>
                <article class="subpanel">
                  <h3>Generation summary</h3>
                  <dl class="summary-list">
                    <div><dt>TTFT</dt><dd>{String(latestTurn?.time_to_first_token_seconds ?? "Unavailable")}</dd></div>
                    <div><dt>Request latency</dt><dd>{String(latestTurn?.request_latency_seconds ?? "Unavailable")}</dd></div>
                    <div><dt>Output tokens</dt><dd>{String(latestTurn?.completion_tokens ?? "Unavailable")}</dd></div>
                    <div><dt>Stop reason</dt><dd>{String(latestTurn?.stop_reason ?? "Unavailable")}</dd></div>
                  </dl>
                </article>
                <article class="subpanel">
                  <h3>Runtime summary</h3>
                  <dl class="summary-list">
                    <div><dt>GPU util</dt><dd>{String(detail.latest_runtime?.gpu?.utilization_percent ?? "Unavailable")}</dd></div>
                    <div><dt>VRAM used</dt><dd>{String(detail.latest_runtime?.gpu?.vram_used_bytes ?? "Unavailable")}</dd></div>
                    <div><dt>KV util</dt><dd>{String(detail.latest_runtime?.kv_cache?.utilization_ratio ?? "Unavailable")}</dd></div>
                    <div><dt>Live tok/s</dt><dd>{String(detail.latest_runtime?.throughput?.tokens_generated_per_second ?? "Unavailable")}</dd></div>
                  </dl>
                </article>
              </section>

              <section class="chart-grid">
                <MetricChart
                  title="Throughput"
                  seriesLabel="tok/s"
                  samples={detail.runtime_history}
                  readValue={(sample) => sample.throughput?.tokens_generated_per_second}
                />
                <MetricChart
                  title="GPU util"
                  seriesLabel="%"
                  samples={detail.runtime_history}
                  readValue={(sample) => sample.gpu?.utilization_percent}
                />
                <MetricChart
                  title="KV cache util"
                  seriesLabel="ratio"
                  samples={detail.runtime_history}
                  readValue={(sample) => sample.kv_cache?.utilization_ratio}
                />
              </section>

              <section class="detail-grid">
                <article class="subpanel">
                  <h3>Load truth</h3>
                  <details open>
                    <summary>Raw JSON</summary>
                    <pre>{pretty(detail.load_report)}</pre>
                  </details>
                </article>
                <article class="subpanel">
                  <h3>Latest runtime</h3>
                  <details open>
                    <summary>Raw JSON</summary>
                    <pre>{pretty(detail.latest_runtime)}</pre>
                  </details>
                </article>
                <article class="subpanel">
                  <h3>Recent turns</h3>
                  <div class="stack">
                    {detail.recent_turns.length === 0 ? <p class="empty-state">No turns captured.</p> : null}
                    {detail.recent_turns.map((turn) => (
                      <div class="list-row" key={String(turn.turn_id)}>
                        <strong>Turn {String(turn.turn_id)}</strong>
                        <span>TTFT {String(turn.time_to_first_token_seconds ?? "Unavailable")}s</span>
                        <span>Out {String(turn.completion_tokens ?? "Unavailable")}</span>
                      </div>
                    ))}
                  </div>
                </article>
                <article class="subpanel">
                  <h3>Logs</h3>
                  <div class="stack">
                    {detail.recent_logs.length === 0 ? <p class="empty-state">No logs captured.</p> : null}
                    {detail.recent_logs
                      .slice()
                      .reverse()
                      .map((log, index) => (
                        <div class="list-row" key={`${String(log.ts)}-${index}`}>
                          <strong>{String(log.source ?? "log")}</strong>
                          <span>{String(log.message ?? "")}</span>
                        </div>
                      ))}
                  </div>
                </article>
                <article class="subpanel full-width">
                  <h3>Inspect</h3>
                  <details>
                    <summary>Raw inspect JSON</summary>
                    <pre>{pretty(detail.inspect)}</pre>
                  </details>
                </article>
              </section>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
