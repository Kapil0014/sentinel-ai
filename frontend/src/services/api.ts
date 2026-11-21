import type { Readiness } from "../types/health";

export class ApiError extends Error {}

/**
 * Fetch readiness. A 503 is a *valid answer* ("not ready", with per-dependency detail),
 * so it is returned as data. Only an unreachable backend or a malformed body throws.
 */
export async function fetchReadiness(signal?: AbortSignal): Promise<Readiness> {
  let response: Response;
  try {
    response = await fetch("/api/health/ready", { signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError("Cannot reach the backend API.");
  }
  if (response.status !== 200 && response.status !== 503) {
    throw new ApiError(`Backend returned an unexpected status (${response.status}).`);
  }
  try {
    return (await response.json()) as Readiness;
  } catch {
    throw new ApiError("Backend returned an invalid response.");
  }
}
