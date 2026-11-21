import { chromium } from "playwright";

export interface SmokeResult {
  status: "ok" | "error";
  browser: string;
  version?: string;
  durationMs: number;
  checkedAt: string;
  error?: string;
}

export type SmokeRunner = () => Promise<SmokeResult>;

/** Launches headless Chromium, opens about:blank, closes it. Proves the toolchain works. */
export function createChromiumSmoke(opts: {
  sandbox: boolean;
  timeoutMs: number;
}): SmokeRunner {
  return async () => {
    const started = Date.now();
    let browser;
    try {
      browser = await chromium.launch({
        headless: true,
        chromiumSandbox: opts.sandbox,
        timeout: opts.timeoutMs,
      });
      const page = await browser.newPage();
      await page.goto("about:blank", { timeout: opts.timeoutMs });
      return {
        status: "ok",
        browser: "chromium",
        version: browser.version(),
        durationMs: Date.now() - started,
        checkedAt: new Date().toISOString(),
      };
    } catch (err) {
      return {
        status: "error",
        browser: "chromium",
        durationMs: Date.now() - started,
        checkedAt: new Date().toISOString(),
        error: (err instanceof Error ? err.message : String(err)).split("\n")[0]?.slice(0, 300),
      };
    } finally {
      await browser?.close().catch(() => undefined);
    }
  };
}

/** Caches results so frequent probes cannot trigger a browser launch each time. */
export function cached(run: SmokeRunner, ttlMs: number, now: () => number = Date.now): SmokeRunner {
  let last: { at: number; value: SmokeResult } | undefined;
  let inflight: Promise<SmokeResult> | undefined;
  return async () => {
    if (last && now() - last.at < ttlMs) return last.value;
    inflight ??= run()
      .then((value) => {
        last = { at: now(), value };
        return value;
      })
      .finally(() => {
        inflight = undefined;
      });
    return inflight;
  };
}
