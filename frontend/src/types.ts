export type SessionSummary = {
  session_id: string;
  status: string;
  backend_name: string | null;
  resolved_model_id: string | null;
  started_at: string | null;
  ended_at: string | null;
  last_event_at: string | null;
  has_errors: boolean;
};

export type RuntimeSample = {
  session_id: string;
  ts: string;
  gpu?: {
    utilization_percent?: number;
    vram_used_bytes?: number;
  };
  kv_cache?: {
    utilization_ratio?: number;
  };
  throughput?: {
    tokens_generated_per_second?: number;
  };
};

export type SessionDetail = {
  session: SessionSummary;
  load_report: Record<string, unknown> | null;
  latest_runtime: RuntimeSample | null;
  runtime_history: RuntimeSample[];
  recent_turns: Array<Record<string, unknown>>;
  recent_logs: Array<Record<string, unknown>>;
  inspect: Record<string, unknown>;
};

export type SseEnvelope = {
  schema_version: string;
  event_id: string;
  ts: string;
  session_id: string;
  backend_name: string | null;
  resolved_model_id: string | null;
  experiment_id: string | null;
  payload: Record<string, unknown>;
};
