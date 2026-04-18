/**
 * App.jsx — Routing principal OW Coach
 * Design inspiré Overwatch 2 — dark navy + orange accent + typographie Rajdhani
 */
import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, NavLink, Navigate, useNavigate } from "react-router-dom";
import useAppStore from "./store/useAppStore";
import SearchModal from "./components/SearchModal";

import CounterPicker from "./pages/CounterPicker";
import Guide        from "./pages/Guide";
import TierList     from "./pages/TierList";
import Tracker      from "./pages/Tracker";
import Coach        from "./pages/Coach";
import Profile      from "./pages/Profile";

const NAV_LINKS = [
  { to: "/counter", label: "Counter",  icon: "⚔" },
  { to: "/guide",   label: "Guide",    icon: "🗺" },
  { to: "/tiers",   label: "Tier List",icon: "📊" },
  { to: "/tracker", label: "Tracker",  icon: "📈" },
  { to: "/coach",   label: "Coach IA", icon: "🤖" },
  { to: "/profile", label: "Profil",   icon: "👤" },
];

function OWLogo() {
  return (
    <svg viewBox="0 0 40 40" fill="none" className="w-8 h-8" xmlns="http://www.w3.org/2000/svg">
      <polygon points="20,2 36,11 36,29 20,38 4,29 4,11" fill="none" stroke="#F4922B" strokeWidth="2"/>
      <polygon points="20,8 30,14 30,26 20,32 10,26 10,14" fill="#F4922B" opacity="0.15"/>
      <text x="20" y="25" textAnchor="middle" fill="#F4922B" fontSize="14" fontWeight="bold" fontFamily="Rajdhani">OW</text>
    </svg>
  );
}

function Navbar({ onSearch }) {
  const { user, logout, overlayMode, toggleOverlay } = useAppStore();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <nav
      className="sticky top-0 z-50 transition-all duration-300"
      style={{
        background: scrolled
          ? "rgba(4,7,15,0.95)"
          : "rgba(4,7,15,0.80)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(244,146,43,0.2)",
        boxShadow: scrolled ? "0 4px 30px rgba(0,0,0,0.5)" : "none",
      }}
    >
      {/* Ligne orange décorative en haut */}
      <div className="h-[2px] w-full" style={{ background: "linear-gradient(90deg, transparent, #F4922B, transparent)" }} />

      <div className="flex items-center gap-6 px-6 py-3">

        {/* Logo */}
        <NavLink to="/counter" className="flex items-center gap-2.5 shrink-0 group">
          <OWLogo />
          <div className="flex flex-col leading-none">
            <span
              className="font-bold text-white text-lg tracking-widest uppercase group-hover:text-ow-accent transition-colors"
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              OW Coach
            </span>
            <span className="text-[9px] tracking-[0.25em] uppercase text-ow-accent/60">
              Stratégie & Analyse
            </span>
          </div>
        </NavLink>

        {/* Séparateur vertical */}
        <div className="h-8 w-px bg-ow-border shrink-0" />

        {/* Bouton recherche */}
        <button
          onClick={onSearch}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 text-gray-500 hover:text-gray-300 transition-colors border border-ow-border hover:border-gray-600"
          style={{ clipPath: "polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%)", fontFamily: "Barlow, sans-serif", fontSize: "12px", minWidth: "160px" }}
          title="Ctrl+K"
        >
          <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span className="flex-1 text-left">Rechercher...</span>
          <kbd className="text-[10px] border border-ow-border px-1.5 py-0.5 text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>Ctrl K</kbd>
        </button>

        {/* Navigation */}
        <div className="flex gap-0.5 flex-1">
          {NAV_LINKS.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `relative px-4 py-2 text-sm font-semibold tracking-widest uppercase transition-all duration-200 ${
                  isActive
                    ? "text-ow-accent"
                    : "text-gray-400 hover:text-white"
                }`
              }
              style={{ fontFamily: "Rajdhani, sans-serif" }}
            >
              {({ isActive }) => (
                <>
                  {label}
                  {/* Indicateur actif */}
                  {isActive && (
                    <span
                      className="absolute bottom-0 left-0 right-0 h-[2px]"
                      style={{ background: "linear-gradient(90deg, transparent, #F4922B, transparent)" }}
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </div>

        {/* Overlay toggle */}
        <button
          onClick={toggleOverlay}
          title="Mode overlay (Alt+O)"
          className={`px-3 py-1.5 text-xs font-bold tracking-widest uppercase transition-all duration-200 border ${
            overlayMode
              ? "border-ow-accent text-ow-accent bg-ow-accent/10 ow-glow"
              : "border-ow-border text-gray-500 hover:text-gray-300 hover:border-gray-500"
          }`}
          style={{ fontFamily: "Rajdhani, sans-serif", clipPath: "polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%)" }}
        >
          Overlay
        </button>

        {/* Auth */}
        {user ? (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-400" style={{ fontFamily: "Barlow, sans-serif" }}>
              {user.username}
            </span>
            <button onClick={logout} className="btn-secondary text-xs py-1.5 px-4">
              Déconnexion
            </button>
          </div>
        ) : (
          <NavLink to="/profile" className="btn-primary text-xs py-1.5 px-4">
            Connexion
          </NavLink>
        )}
      </div>
    </nav>
  );
}

export default function App() {
  const { overlayMode, toggleOverlay } = useAppStore();
  const [searchOpen, setSearchOpen] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      if (e.altKey && e.key === "o") toggleOverlay();
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
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
        <Navbar onSearch={() => setSearchOpen(true)} />
        <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
        <main className="px-6 py-6 max-w-7xl mx-auto">
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
