import { describe, expect, it } from "vitest";
import { loadConfig } from "../src/config.js";

describe("loadConfig", () => {
  it("uses safe defaults", () => {
    const c = loadConfig({});
    expect(c.port).toBe(8081);
    expect(c.chromiumSandbox).toBe(true); // sandbox ON unless explicitly disabled
    expect(c.logLevel).toBe("info");
  });

  it("reads overrides", () => {
    const c = loadConfig({ PORT: "9000", CHROMIUM_SANDBOX: "false", LOG_LEVEL: "DEBUG" });
    expect(c).toMatchObject({ port: 9000, chromiumSandbox: false, logLevel: "debug" });
  });

  it.each([["abc"], ["0"], ["-5"], ["1.5"], ["70000"]])("rejects invalid PORT %s", (port) => {
    expect(() => loadConfig({ PORT: port })).toThrow(/PORT/);
  });

  it("rejects a non-boolean CHROMIUM_SANDBOX instead of guessing", () => {
    expect(() => loadConfig({ CHROMIUM_SANDBOX: "yes" })).toThrow(/CHROMIUM_SANDBOX/);
  });
});
