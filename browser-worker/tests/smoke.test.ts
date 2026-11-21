import { describe, expect, it } from "vitest";
import { cached, createChromiumSmoke, type SmokeResult } from "../src/browserSmoke.js";

const result = (n: number): SmokeResult => ({
  status: "ok", browser: "chromium", durationMs: n, checkedAt: "t",
});

describe("cached smoke runner", () => {
  it("reuses a fresh result and refreshes after the TTL", async () => {
    let calls = 0;
    let clock = 0;
    const run = cached(async () => result(++calls), 1000, () => clock);
    expect((await run()).durationMs).toBe(1);
    clock = 999;
    expect((await run()).durationMs).toBe(1);
    clock = 1000;
    expect((await run()).durationMs).toBe(2);
  });

  it("shares one in-flight launch between concurrent callers", async () => {
    let calls = 0;
    const run = cached(async () => { calls++; await new Promise((r) => setTimeout(r, 20)); return result(calls); }, 1000);
    await Promise.all([run(), run(), run()]);
    expect(calls).toBe(1);
  });
});

// Real Chromium launch. Opt-in locally; CI installs browsers and sets RUN_BROWSER_TESTS=1.
describe.skipIf(process.env.RUN_BROWSER_TESTS !== "1")("real Chromium", () => {
  const sandbox = process.env.CHROMIUM_SANDBOX !== "false";

  it("launches headless Chromium and reports its version", async () => {
    const res = await createChromiumSmoke({ sandbox, timeoutMs: 30_000 })();
    expect(res.error).toBeUndefined();
    expect(res.status).toBe("ok");
    expect(res.version).toMatch(/^\d+\./);
  });
});
