import { createChromiumSmoke, cached } from "./browserSmoke.js";
import { loadConfig } from "./config.js";
import { buildServer } from "./server.js";

let config;
try {
  config = loadConfig();
} catch (err) {
  process.stderr.write(`Invalid configuration:\n  - ${(err as Error).message}\n`);
  process.exit(1);
}

const smoke = cached(
  createChromiumSmoke({ sandbox: config.chromiumSandbox, timeoutMs: config.smokeTimeoutMs }),
  config.smokeCacheTtlMs,
);
const app = buildServer({ config, smoke });

if (!config.chromiumSandbox) {
  app.log.warn("CHROMIUM_SANDBOX=false: Chromium sandbox is disabled. Do not use in production.");
}

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    app.log.info({ signal }, "shutting_down");
    void app.close().then(() => process.exit(0));
  });
}

app.listen({ port: config.port, host: config.host }).catch((err) => {
  app.log.error(err, "failed_to_start");
  process.exit(1);
});
