import { Link, NavLink } from "react-router-dom";

function navClass({ isActive }) {
  return [
    "rounded-full px-4 py-2 text-sm font-medium transition",
    isActive
      ? "bg-ink text-white shadow-card"
      : "bg-white/60 text-ink hover:bg-white"
  ].join(" ");
}

export default function AppLayout({ children }) {
  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      <header className="mb-6 rounded-3xl border border-ink/10 bg-panel/90 p-5 shadow-card backdrop-blur">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <Link to="/" className="font-serif text-3xl font-bold tracking-tight text-ink">
              Book Insight
            </Link>
            <p className="mt-1 text-sm text-ink/70">
              Intelligent book dashboard, recommendations, and question answering
            </p>
          </div>
          <nav className="flex gap-2">
            <NavLink to="/" end className={navClass}>
              Dashboard
            </NavLink>
            <NavLink to="/qa" className={navClass}>
              Ask Questions
            </NavLink>
          </nav>
        </div>
      </header>

      <main className="flex-1">{children}</main>
    </div>
  );
}
