/** Mirrors the backend's /api/health/ready response (backend/app/api/health.py). */
export interface HealthCheck {
  name: string;
  status: "ok" | "error";
  required: boolean;
  latency_ms: number;
  detail: string | null;
}

export interface Readiness {
  status: "ready" | "not_ready";
  environment: string;
  checks: HealthCheck[];
}
