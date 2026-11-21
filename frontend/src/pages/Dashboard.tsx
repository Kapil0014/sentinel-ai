import { SystemStatus } from "../components/SystemStatus";

export function Dashboard() {
  return (
    <div className="max-w-3xl space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-neutral-500">
          Autonomous AI software testing and bug detection.
        </p>
      </header>

      <SystemStatus />

      {/* Honest empty state: real statistics arrive with the session APIs (Week 2+). */}
      <section className="rounded-lg border border-dashed border-neutral-300 p-6 text-sm text-neutral-500 dark:border-neutral-700">
        <h2 className="font-semibold text-neutral-700 dark:text-neutral-300">
          No testing sessions yet
        </h2>
        <p className="mt-1">
          Session statistics, pass/fail charts and recent activity will appear here once testing
          sessions can be created (planned for Weeks 2 to 6).
        </p>
      </section>
    </div>
  );
}
