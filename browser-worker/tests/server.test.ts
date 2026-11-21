import { afterEach, describe, expect, it } from "vitest";
import type { FastifyInstance } from "fastify";
import type { SmokeResult } from "../src/browserSmoke.js";
import { buildServer } from "../src/server.js";

const ok: SmokeResult = {
  status: "ok", browser: "chromium", version: "1.0", durationMs: 5, checkedAt: "2026-01-01T00:00:00Z",
};
const bad: SmokeResult = {
  status: "error", browser: "chromium", durationMs: 5, checkedAt: "2026-01-01T00:00:00Z", error: "launch failed",
};

let app: FastifyInstance;
const make = (smoke: () => Promise<SmokeResult>) =>
  (app = buildServer({ config: { logLevel: "silent" }, smoke }));

afterEach(async () => app?.close());

describe("GET /health (liveness)", () => {
  it("returns ok and never launches a browser", async () => {
    let launches = 0;
    make(async () => { launches++; return ok; });
    const res = await app.inject("/health");
    expect(res.statusCode).toBe(200);
    expect(res.json()).toMatchObject({ status: "ok", service: "sentinel-browser-worker" });
    expect(launches).toBe(0);
  });
});

describe("GET /health/ready (readiness)", () => {
  it("is 200 when Chromium launches", async () => {
    make(async () => ok);
    const res = await app.inject("/health/ready");
    expect(res.statusCode).toBe(200);
    expect(res.json().status).toBe("ready");
  });

  it("is 503 when Chromium cannot launch, with the reason", async () => {
    make(async () => bad);
    const res = await app.inject("/health/ready");
    expect(res.statusCode).toBe(503);
    expect(res.json()).toMatchObject({ status: "not_ready", checks: { chromium: { error: "launch failed" } } });
  });
});

describe("request IDs", () => {
  it("generates one when absent", async () => {
    make(async () => ok);
    const res = await app.inject("/health");
    expect(res.headers["x-request-id"]).toMatch(/^[0-9a-f]{32}$/);
  });

  it("echoes a valid incoming ID", async () => {
    make(async () => ok);
    const res = await app.inject({ url: "/health", headers: { "x-request-id": "trace-12345678" } });
    expect(res.headers["x-request-id"]).toBe("trace-12345678");
  });

  it("replaces a malformed ID", async () => {
    make(async () => ok);
    const res = await app.inject({ url: "/health", headers: { "x-request-id": "bad id!" } });
    expect(res.headers["x-request-id"]).toMatch(/^[0-9a-f]{32}$/);
  });
});
