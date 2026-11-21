interface PlannedProps {
  title: string;
  week: number;
  description: string;
}

/** Placeholder for a page that is not implemented yet. Deliberately shows no fake data. */
export function Planned({ title, week, description }: PlannedProps) {
  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
      <p className="mt-3 inline-block rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-300">
        Not implemented yet (planned for Week {week})
      </p>
      <p className="mt-4 text-sm text-neutral-600 dark:text-neutral-400">{description}</p>
    </div>
  );
}

export function NotFound() {
  return (
    <div>
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="mt-2 text-sm text-neutral-500">That address does not exist.</p>
    </div>
  );
}
