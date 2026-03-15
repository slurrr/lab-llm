import { useEffect, useMemo, useState } from "preact/hooks";

import { MetricChart } from "./chart";
import type { SessionDetail, SessionSummary, SseEnvelope } from "./types";

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

export function App() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SessionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshSessions() {
    const payload = await fetchJson<{ sessions: SessionSummary[] }>("/api/sessions");
    setSessions(payload.sessions);
    setSelectedSessionId((current) => current ?? payload.sessions[0]?.session_id ?? null);
  }

  async function refreshDetail(sessionId: string) {
    const payload = await fetchJson<SessionDetail>(`/api/sessions/${sessionId}`);
    setDetail(payload);
  }

  useEffect(() => {
    refreshSessions().catch((err: Error) => setError(err.message));
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
    const reload = () => {
      refreshSessions().catch((err: Error) => setError(err.message));
      if (selectedSessionId) {
        refreshDetail(selectedSessionId).catch((err: Error) => setError(err.message));
      }
    };
    source.addEventListener("runtime_sample", reload);
    source.addEventListener("turn_finished", reload);
    source.addEventListener("session_started", reload);
    source.addEventListener("session_finished", reload);
    source.addEventListener("log_recorded", reload);
    source.addEventListener("error_reported", reload);
    source.addEventListener("connected", () => setError(null));
    source.onerror = () => setError("Live event stream disconnected.");
    return () => {
      source.close();
    };
  }, [selectedSessionId]);

  const selectedSession = useMemo(
    () => sessions.find((session) => session.session_id === selectedSessionId) ?? null,
    [selectedSessionId, sessions]
  );

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
                  <pre>{pretty(detail.load_report)}</pre>
                </article>
                <article class="subpanel">
                  <h3>Latest runtime</h3>
                  <pre>{pretty(detail.latest_runtime)}</pre>
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
                  <pre>{pretty(detail.inspect)}</pre>
                </article>
              </section>
            </>
          )}
        </section>
      </main>
    </div>
  );
}
