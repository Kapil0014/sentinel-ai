import { useEffect, useState } from "react";
import { ApiError, fetchReadiness } from "../services/api";
import type { Readiness } from "../types/health";

export type ReadinessState =
  | { phase: "loading" }
  | { phase: "loaded"; data: Readiness }
  | { phase: "unreachable"; message: string };

/** Polls backend readiness. Cleans up its timer and in-flight request on unmount. */
export function useReadiness(intervalMs = 10_000): ReadinessState {
  const [state, setState] = useState<ReadinessState>({ phase: "loading" });

  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;

    const tick = async () => {
      try {
        const data = await fetchReadiness(controller.signal);
        setState({ phase: "loaded", data });
      } catch (err) {
        if (controller.signal.aborted) return;
        setState({
          phase: "unreachable",
          message: err instanceof ApiError ? err.message : "Unexpected error.",
        });
      }
      if (!controller.signal.aborted) timer = setTimeout(tick, intervalMs);
    };
    void tick();

    return () => {
      controller.abort();
      if (timer) clearTimeout(timer);
    };
  }, [intervalMs]);

  return state;
}
