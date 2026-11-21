import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";

beforeEach(() => {
  vi.spyOn(globalThis, "fetch").mockReturnValue(new Promise(() => undefined));
});

const at = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>,
  );

describe("routing", () => {
  it("renders the dashboard with the system status panel and an honest empty state", () => {
    at("/");
    expect(screen.getByRole("heading", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "System status" })).toBeInTheDocument();
    expect(screen.getByText(/no testing sessions yet/i)).toBeInTheDocument();
  });

  it.each([
    ["/sessions/new", "New testing session", 6],
    ["/sessions", "Sessions", 6],
    ["/tests", "Test cases", 3],
    ["/bugs", "Bug reports", 5],
    ["/settings", "Settings", 6],
  ])("marks %s as not implemented with its planned week", (path, title, week) => {
    at(path);
    expect(screen.getByRole("heading", { name: title })).toBeInTheDocument();
    expect(screen.getByText(`Not implemented yet (planned for Week ${week})`)).toBeInTheDocument();
  });

  it("shows a not-found page for unknown routes", () => {
    at("/does-not-exist");
    expect(screen.getByRole("heading", { name: /page not found/i })).toBeInTheDocument();
  });

  it("lists every section in the sidebar navigation", () => {
    at("/");
    const nav = screen.getByRole("navigation", { name: "Primary" });
    for (const label of ["Dashboard", "New session", "Sessions", "Test cases", "Bug reports", "Settings"]) {
      expect(nav).toHaveTextContent(label);
    }
  });
});
