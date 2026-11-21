import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { SystemStatus } from "../src/components/SystemStatus";
import type { Readiness } from "../src/types/health";

const check = (name: string, status: "ok" | "error", required = true, detail: string | null = null) => ({
  name, status, required, latency_ms: 3, detail,
});

function mockFetch(status: number, body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(typeof body === "string" ? body : JSON.stringify(body), { status }),
  );
}

describe("SystemStatus", () => {
  it("shows a loading state first", () => {
    vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => undefined));
    render(<SystemStatus />);
    expect(screen.getByText(/checking services/i)).toBeInTheDocument();
  });

  it("shows real per-service status when ready", async () => {
    const body: Readiness = {
      status: "ready",
      environment: "development",
      checks: [check("database", "ok"), check("redis", "ok"), check("browser_worker", "ok", false)],
    };
    const spy = mockFetch(200, body);
    render(<SystemStatus />);
    expect(await screen.findByText(/all required services are ready/i)).toBeInTheDocument();
    expect(screen.getByText("PostgreSQL")).toBeInTheDocument();
    expect(screen.getAllByText("Operational")).toHaveLength(3);
    expect(screen.getByText("optional")).toBeInTheDocument();
    expect(spy).toHaveBeenCalledWith("/api/health/ready", expect.anything());
  });

  it("treats a 503 as 'not ready' data and shows which dependency failed", async () => {
    mockFetch(503, {
      status: "not_ready",
      environment: "development",
      checks: [check("database", "error", true, "OperationalError: connection refused"), check("redis", "ok")],
    });
    render(<SystemStatus />);
    expect(await screen.findByText(/not ready/i)).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
    expect(screen.getByText(/connection refused/i)).toBeInTheDocument();
  });

  it("shows an alert when the backend is unreachable", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    render(<SystemStatus />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/cannot reach the backend/i);
  });

  it("shows an alert for an unexpected HTTP status", async () => {
    mockFetch(500, "boom");
    render(<SystemStatus />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/unexpected status \(500\)/i);
  });

  it("shows an alert for a malformed body", async () => {
    mockFetch(200, "not json");
    render(<SystemStatus />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/invalid response/i);
  });

  it("polls again after the interval and picks up recovery", async () => {
    const down = new Response(
      JSON.stringify({ status: "not_ready", environment: "development", checks: [check("redis", "error")] }),
      { status: 503 },
    );
    const up = new Response(
      JSON.stringify({ status: "ready", environment: "development", checks: [check("redis", "ok")] }),
      { status: 200 },
    );
    const spy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(down).mockResolvedValue(up);
    render(<SystemStatus intervalMs={20} />);
    expect(await screen.findByText(/not ready/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText(/all required services are ready/i)).toBeInTheDocument());
    expect(spy.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  it("stops polling after unmount", async () => {
    const spy = mockFetch(200, { status: "ready", environment: "development", checks: [] });
    const { unmount } = render(<SystemStatus intervalMs={20} />);
    await screen.findByText(/all required services are ready/i);
    unmount();
    const calls = spy.mock.calls.length;
    await new Promise((r) => setTimeout(r, 80));
    expect(spy.mock.calls.length).toBe(calls);
  });
});
