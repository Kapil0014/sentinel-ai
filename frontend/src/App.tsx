import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { Dashboard } from "./pages/Dashboard";
import { NotFound, Planned } from "./pages/Planned";

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route
          path="sessions/new"
          element={
            <Planned
              title="New testing session"
              week={6}
              description="Enter a URL, choose AI-Assisted or Autonomous mode, and set crawl limits."
            />
          }
        />
        <Route
          path="sessions"
          element={
            <Planned title="Sessions" week={6} description="History of testing sessions and live monitoring." />
          }
        />
        <Route
          path="tests"
          element={
            <Planned
              title="Test cases"
              week={3}
              description="Review, edit and approve AI-generated test cases before they run."
            />
          }
        />
        <Route
          path="bugs"
          element={
            <Planned title="Bug reports" week={5} description="Confirmed and suspected bugs with supporting evidence." />
          }
        />
        <Route
          path="settings"
          element={
            <Planned title="Settings" week={6} description="Execution limits and safety settings. API keys are never shown in the browser." />
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
