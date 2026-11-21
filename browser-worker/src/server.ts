import { randomUUID } from "node:crypto";
import Fastify, { LogController, type FastifyInstance } from "fastify";
import type { SmokeRunner } from "./browserSmoke.js";
import type { WorkerConfig } from "./config.js";

export const SERVICE_NAME = "sentinel-browser-worker";
export const SERVICE_VERSION = "0.1.0";

const VALID_REQUEST_ID = /^[A-Za-z0-9._-]{8,64}$/;

export interface ServerDeps {
  config: Pick<WorkerConfig, "logLevel">;
  smoke: SmokeRunner;
}

export function buildServer(deps: ServerDeps): FastifyInstance {
  const app = Fastify({
    logger: { level: deps.config.logLevel },
    // We emit one structured request_completed line ourselves (see onResponse below).
    logController: new LogController({ disableRequestLogging: true }),
    // Same request-ID rules as the backend: accept only short, boring IDs.
    genReqId: (req) => {
      const incoming = req.headers["x-request-id"];
      return typeof incoming === "string" && VALID_REQUEST_ID.test(incoming)
        ? incoming
        : randomUUID().replaceAll("-", "");
    },
  });

  app.addHook("onSend", async (req, reply) => {
    reply.header("x-request-id", req.id);
  });
  app.addHook("onResponse", async (req, reply) => {
    req.log.info(
      { method: req.method, path: req.url, statusCode: reply.statusCode, durationMs: Math.round(reply.elapsedTime * 100) / 100 },
      "request_completed",
    );
  });

  const startedAt = Date.now();

  // Liveness: no browser launch, never flaps with Chromium problems.
  app.get("/health", async () => ({
    status: "ok" as const,
    service: SERVICE_NAME,
    version: SERVICE_VERSION,
    uptimeSeconds: Math.round((Date.now() - startedAt) / 1000),
  }));

  // Readiness: proves Chromium can actually launch in this container.
  app.get("/health/ready", async (_req, reply) => {
    const result = await deps.smoke();
    if (result.status !== "ok") reply.code(503);
    return { status: result.status === "ok" ? "ready" : "not_ready", checks: { chromium: result } };
  });

  return app;
}
