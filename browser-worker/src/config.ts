/** Worker configuration, read from environment variables with validation. */

export interface WorkerConfig {
  port: number;
  host: string;
  logLevel: string;
  /** Chromium's own sandbox. Must be true in production; see docs/security.md. */
  chromiumSandbox: boolean;
  smokeCacheTtlMs: number;
  smokeTimeoutMs: number;
}

function parseIntStrict(name: string, raw: string | undefined, fallback: number): number {
  if (raw === undefined || raw === "") return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) {
    throw new Error(`${name} must be a positive integer, got "${raw}"`);
  }
  return value;
}

function parseBool(name: string, raw: string | undefined, fallback: boolean): boolean {
  if (raw === undefined || raw === "") return fallback;
  if (raw === "true") return true;
  if (raw === "false") return false;
  throw new Error(`${name} must be "true" or "false", got "${raw}"`);
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): WorkerConfig {
  const port = parseIntStrict("PORT", env.PORT, 8081);
  if (port > 65535) throw new Error(`PORT must be <= 65535, got ${port}`);
  return {
    port,
    host: env.HOST || "0.0.0.0",
    logLevel: env.LOG_LEVEL?.toLowerCase() || "info",
    chromiumSandbox: parseBool("CHROMIUM_SANDBOX", env.CHROMIUM_SANDBOX, true),
    smokeCacheTtlMs: parseIntStrict("SMOKE_CACHE_TTL_MS", env.SMOKE_CACHE_TTL_MS, 30_000),
    smokeTimeoutMs: parseIntStrict("SMOKE_TIMEOUT_MS", env.SMOKE_TIMEOUT_MS, 20_000),
  };
}
