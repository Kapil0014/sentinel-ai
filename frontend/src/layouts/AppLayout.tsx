import { NavLink, Outlet } from "react-router-dom";

export const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/sessions/new", label: "New session" },
  { to: "/sessions", label: "Sessions" },
  { to: "/tests", label: "Test cases" },
  { to: "/bugs", label: "Bug reports" },
  { to: "/settings", label: "Settings" },
] as const;

export function AppLayout() {
  return (
    <div className="flex min-h-screen bg-white text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100">
      <aside className="w-56 shrink-0 border-r border-neutral-200 p-4 dark:border-neutral-800">
        <p className="mb-6 text-lg font-semibold tracking-tight">Sentinel AI</p>
        <nav aria-label="Primary" className="flex flex-col gap-1 text-sm">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={"end" in item ? item.end : false}
              className={({ isActive }) =>
                `rounded px-3 py-2 ${
                  isActive
                    ? "bg-neutral-100 font-medium dark:bg-neutral-800"
                    : "text-neutral-600 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-900"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
