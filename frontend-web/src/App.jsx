/**
 * App.jsx — Routing principal OW Coach
 * Gère la navigation, la navbar et le mode overlay (Alt+O).
 */
import { useEffect } from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import useAppStore from "./store/useAppStore";

import CounterPicker from "./pages/CounterPicker";
import Guide        from "./pages/Guide";
import TierList     from "./pages/TierList";
import Tracker      from "./pages/Tracker";
import Coach        from "./pages/Coach";
import Profile      from "./pages/Profile";

// Liens de navigation principaux
const NAV_LINKS = [
  { to: "/counter", label: "Counter" },
  { to: "/guide",   label: "Guide" },
  { to: "/tiers",   label: "Tier List" },
  { to: "/tracker", label: "Tracker" },
  { to: "/coach",   label: "Coach IA" },
  { to: "/profile", label: "Profil" },
];

function Navbar() {
  const { user, logout, overlayMode, toggleOverlay } = useAppStore();

  return (
    <nav className="bg-ow-surface border-b border-ow-border px-4 py-3 flex items-center gap-4 sticky top-0 z-50">
      {/* Logo */}
      <span className="text-ow-accent font-bold text-lg mr-4">⚔ OW Coach</span>

      {/* Liens */}
      <div className="flex gap-1 flex-1">
        {NAV_LINKS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-ow-accent text-white"
                  : "text-gray-400 hover:text-white hover:bg-ow-border"
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </div>

      {/* Overlay toggle */}
      <button
        onClick={toggleOverlay}
        title="Mode overlay (Alt+O)"
        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
          overlayMode
            ? "border-ow-accent text-ow-accent bg-ow-accent/10"
            : "border-ow-border text-gray-400 hover:text-white"
        }`}
      >
        Overlay
      </button>

      {/* Auth */}
      {user ? (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">{user.username}</span>
          <button onClick={logout} className="btn-secondary text-sm py-1 px-3">
            Déconnexion
          </button>
        </div>
      ) : (
        <NavLink to="/profile" className="btn-primary text-sm py-1 px-3">
          Connexion
        </NavLink>
      )}
    </nav>
  );
}

export default function App() {
  const { overlayMode, toggleOverlay } = useAppStore();

  // Raccourci clavier Alt+O pour basculer le mode overlay
  useEffect(() => {
    const handler = (e) => {
      if (e.altKey && e.key === "o") toggleOverlay();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [toggleOverlay]);

  return (
    <BrowserRouter>
      <div
        className={`min-h-screen bg-ow-bg transition-all duration-300 ${
          overlayMode ? "max-w-[400px] ml-auto" : ""
        }`}
      >
        <Navbar />

        <main className="p-4">
          <Routes>
            <Route path="/"        element={<Navigate to="/counter" replace />} />
            <Route path="/counter" element={<CounterPicker />} />
            <Route path="/guide"   element={<Guide />} />
            <Route path="/tiers"   element={<TierList />} />
            <Route path="/tracker" element={<Tracker />} />
            <Route path="/coach"   element={<Coach />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
