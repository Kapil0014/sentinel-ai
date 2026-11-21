import { useReadiness } from "../hooks/useReadiness";
import type { HealthCheck } from "../types/health";

const LABELS: Record<string, string> = {
  database: "PostgreSQL",
  redis: "Redis",
  browser_worker: "Browser worker",
};

function CheckRow({ check }: { check: HealthCheck }) {
  const ok = check.status === "ok";
  return (
    <li className="flex items-start justify-between gap-4 py-2">
      <div>
        <span className="font-medium">{LABELS[check.name] ?? check.name}</span>
        {!check.required && <span className="ml-2 text-xs text-neutral-500">optional</span>}
        {!ok && check.detail && (
          <p className="mt-0.5 text-xs text-neutral-500 break-all">{check.detail}</p>
        )}
      </div>
      <span
        className={ok ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}
      >
        {ok ? "Operational" : "Unavailable"}
      </span>
    </li>
  );
}

export function SystemStatus({ intervalMs }: { intervalMs?: number }) {
  const state = useReadiness(intervalMs);

  return (
    <section
      aria-labelledby="system-status-heading"
      className="rounded-lg border border-neutral-200 p-4 dark:border-neutral-800"
    >
      <h2 id="system-status-heading" className="text-sm font-semibold">
        System status
      </h2>

      {state.phase === "loading" && (
        <p className="mt-3 text-sm text-neutral-500">Checking services…</p>
      )}

      {state.phase === "unreachable" && (
        <p role="alert" className="mt-3 text-sm text-red-600 dark:text-red-400">
          {state.message} Is the backend running?
        </p>
      )}

      {state.phase === "loaded" && (
        <>
          <p
            className={`mt-3 text-sm font-medium ${
              state.data.status === "ready"
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {state.data.status === "ready" ? "All required services are ready" : "Not ready"}
            <span className="ml-2 font-normal text-neutral-500">({state.data.environment})</span>
          </p>
          <ul className="mt-2 divide-y divide-neutral-200 text-sm dark:divide-neutral-800">
            {state.data.checks.map((c) => (
              <CheckRow key={c.name} check={c} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
