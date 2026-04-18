/**
 * SearchModal — recherche globale Ctrl+K style OW2.
 * Cherche dans les héros et les maps, navigation au clic.
 */
import { useState, useEffect, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import { getMaps } from "../api/maps";

const ROLE_COLOR  = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };
const DIFF_COLOR  = { 1: "#69db7c", 2: "#F4922B", 3: "#FF4655" };
const DIFF_LABEL  = { 1: "Facile", 2: "Moyen", 3: "Difficile" };
const ROLE_LABEL  = { tank: "Tank", dps: "DPS", support: "Support" };
const TYPE_LABEL  = { escort: "Escorte", control: "Contrôle", hybrid: "Hybride", push: "Push", flashpoint: "Flashpoint", clash: "Clash" };
const TYPE_EMOJI  = { escort: "🚛", control: "🔵", hybrid: "⚡", push: "🤖", flashpoint: "💥", clash: "⚔️" };

export default function SearchModal({ open, onClose }) {
  const navigate  = useNavigate();
  const { heroes } = useAppStore();
  const [maps,    setMaps]    = useState([]);
  const [query,   setQuery]   = useState("");
  const [cursor,  setCursor]  = useState(0);
  const inputRef  = useRef(null);

  // Charger les maps une fois
  useEffect(() => {
    getMaps().then(d => setMaps(d.results ?? d)).catch(() => {});
  }, []);

  // Focus input à l'ouverture
  useEffect(() => {
    if (open) {
      setQuery("");
      setCursor(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  // Filtrage
  const q = query.toLowerCase().trim();
  const filteredHeroes = q.length < 1 ? heroes.slice(0, 6) : heroes.filter(h =>
    h.name.toLowerCase().includes(q) || h.role.toLowerCase().includes(q) || (h.subrole || "").toLowerCase().includes(q)
  ).slice(0, 8);

  const filteredMaps = q.length < 1 ? maps.slice(0, 4) : maps.filter(m =>
    m.name.toLowerCase().includes(q) || (TYPE_LABEL[m.map_type] || "").toLowerCase().includes(q)
  ).slice(0, 6);

  // Résultats combinés pour navigation clavier
  const results = [
    ...filteredHeroes.map(h => ({ type: "hero", data: h })),
    ...filteredMaps.map(m  => ({ type: "map",  data: m })),
  ];

  const go = useCallback((item) => {
    if (item.type === "hero") navigate(`/counter?hero=${item.data.slug}`);
    else                       navigate(`/guide?map=${item.data.slug}`);
    onClose();
  }, [navigate, onClose]);

  // Navigation clavier
  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      if (e.key === "Escape") { onClose(); return; }
      if (e.key === "ArrowDown") { e.preventDefault(); setCursor(c => Math.min(c + 1, results.length - 1)); }
      if (e.key === "ArrowUp")   { e.preventDefault(); setCursor(c => Math.max(c - 1, 0)); }
      if (e.key === "Enter" && results[cursor]) go(results[cursor]);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, results, cursor, go, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[12vh]"
      style={{ background: "rgba(4,7,15,0.85)", backdropFilter: "blur(8px)" }}
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl mx-4"
        onClick={e => e.stopPropagation()}
        style={{
          background: "#0B1221",
          border: "1px solid rgba(244,146,43,0.3)",
          clipPath: "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
          boxShadow: "0 0 40px rgba(244,146,43,0.1), 0 20px 60px rgba(0,0,0,0.6)",
        }}
      >
        {/* Ligne décorative */}
        <div className="h-[1px]" style={{ background: "linear-gradient(90deg, transparent, #F4922B, transparent)" }} />

        {/* Input */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-ow-border">
          <svg className="w-4 h-4 shrink-0" style={{ color: "#F4922B" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            value={query}
            onChange={e => { setQuery(e.target.value); setCursor(0); }}
            placeholder="Rechercher un héros, une map…"
            className="flex-1 bg-transparent text-white placeholder-gray-500 text-sm outline-none"
            style={{ fontFamily: "Barlow, sans-serif" }}
          />
          <span
            className="text-[10px] px-2 py-1 border border-ow-border text-gray-500 shrink-0"
            style={{ fontFamily: "Rajdhani, sans-serif", clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)" }}
          >
            ESC
          </span>
        </div>

        {/* Résultats */}
        <div className="max-h-96 overflow-y-auto">
          {/* Héros */}
          {filteredHeroes.length > 0 && (
            <div>
              <div className="px-4 pt-3 pb-1">
                <span className="text-[10px] tracking-[0.2em] uppercase text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                  Héros
                </span>
              </div>
              {filteredHeroes.map((hero, i) => {
                const idx = i;
                const isActive = cursor === idx;
                return (
                  <button
                    key={hero.slug}
                    onClick={() => go({ type: "hero", data: hero })}
                    onMouseEnter={() => setCursor(idx)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-all"
                    style={{
                      background: isActive ? "rgba(244,146,43,0.08)" : "transparent",
                      borderLeft: isActive ? "2px solid #F4922B" : "2px solid transparent",
                    }}
                  >
                    {/* Portrait */}
                    <div
                      className="w-8 h-8 shrink-0 overflow-hidden flex items-center justify-center"
                      style={{
                        background: "rgba(4,7,15,0.8)",
                        border: `1px solid ${ROLE_COLOR[hero.role] || "#444"}30`,
                        clipPath: "polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 4px 100%, 0 calc(100% - 4px))",
                      }}
                    >
                      {hero.icon_url
                        ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover" />
                        : <span className="text-[10px] font-bold text-white">{hero.name.slice(0, 2).toUpperCase()}</span>
                      }
                    </div>

                    {/* Infos */}
                    <div className="flex-1 min-w-0">
                      <span className="text-sm font-semibold text-white truncate block" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.05em" }}>
                        {highlight(hero.name, q)}
                      </span>
                    </div>

                    {/* Role badge */}
                    <span
                      className="text-[10px] font-bold px-2 py-0.5 shrink-0"
                      style={{
                        color: ROLE_COLOR[hero.role],
                        background: `${ROLE_COLOR[hero.role]}15`,
                        border: `1px solid ${ROLE_COLOR[hero.role]}30`,
                        fontFamily: "Rajdhani, sans-serif",
                        clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
                      }}
                    >
                      {ROLE_LABEL[hero.role]}
                    </span>

                    {/* Difficulté — 3 barres */}
                    {hero.difficulty && (
                      <div className="flex items-center gap-0.5 shrink-0">
                        {[1,2,3].map(i => (
                          <div key={i} className="w-2 h-2" style={{
                            background: i <= hero.difficulty ? DIFF_COLOR[hero.difficulty] : "rgba(255,255,255,0.08)",
                            clipPath: "polygon(2px 0%, 100% 0%, calc(100% - 2px) 100%, 0% 100%)",
                          }} />
                        ))}
                      </div>
                    )}

                    {/* Tier */}
                    {hero.tier && (
                      <span className="text-[10px] font-bold w-5 text-center shrink-0" style={{ color: getTierColor(hero.tier), fontFamily: "Rajdhani, sans-serif" }}>
                        {hero.tier}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}

          {/* Maps */}
          {filteredMaps.length > 0 && (
            <div>
              <div className="px-4 pt-3 pb-1">
                <span className="text-[10px] tracking-[0.2em] uppercase text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                  Maps
                </span>
              </div>
              {filteredMaps.map((map, i) => {
                const idx = filteredHeroes.length + i;
                const isActive = cursor === idx;
                return (
                  <button
                    key={map.slug}
                    onClick={() => go({ type: "map", data: map })}
                    onMouseEnter={() => setCursor(idx)}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-left transition-all"
                    style={{
                      background: isActive ? "rgba(0,194,255,0.06)" : "transparent",
                      borderLeft: isActive ? "2px solid #00C2FF" : "2px solid transparent",
                    }}
                  >
                    <span className="text-lg shrink-0">{TYPE_EMOJI[map.map_type] ?? "🗺"}</span>
                    <span className="flex-1 text-sm font-semibold text-white truncate" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.05em" }}>
                      {highlight(map.name, q)}
                    </span>
                    <span
                      className="text-[10px] font-bold px-2 py-0.5 shrink-0"
                      style={{
                        color: "#00C2FF",
                        background: "rgba(0,194,255,0.1)",
                        border: "1px solid rgba(0,194,255,0.25)",
                        fontFamily: "Rajdhani, sans-serif",
                        clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
                      }}
                    >
                      {TYPE_LABEL[map.map_type] ?? map.map_type}
                    </span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Aucun résultat */}
          {q.length > 0 && filteredHeroes.length === 0 && filteredMaps.length === 0 && (
            <div className="px-4 py-8 text-center text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              Aucun résultat pour « {query} »
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-ow-border flex items-center gap-4">
          {[["↑↓", "Naviguer"], ["↵", "Ouvrir"], ["ESC", "Fermer"]].map(([key, label]) => (
            <span key={key} className="flex items-center gap-1.5 text-[10px] text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              <kbd
                className="px-1.5 py-0.5 border border-ow-border text-gray-500"
                style={{ clipPath: "polygon(3px 0%, 100% 0%, calc(100% - 3px) 100%, 0% 100%)", fontSize: "9px" }}
              >
                {key}
              </kbd>
              {label}
            </span>
          ))}
          <span className="ml-auto text-[10px] text-gray-700" style={{ fontFamily: "Rajdhani, sans-serif" }}>
            {results.length} résultat{results.length > 1 ? "s" : ""}
          </span>
        </div>
      </div>
    </div>
  );
}

// Colorie le texte matchant
function highlight(text, q) {
  if (!q) return text;
  const i = text.toLowerCase().indexOf(q.toLowerCase());
  if (i === -1) return text;
  return (
    <>
      {text.slice(0, i)}
      <mark style={{ background: "rgba(244,146,43,0.3)", color: "#F4922B", borderRadius: "2px" }}>
        {text.slice(i, i + q.length)}
      </mark>
      {text.slice(i + q.length)}
    </>
  );
}

function getTierColor(tier) {
  return { S: "#FF4655", A: "#F4922B", B: "#FFD700", C: "#69db7c", D: "#00C2FF" }[tier] ?? "#aaa";
}
