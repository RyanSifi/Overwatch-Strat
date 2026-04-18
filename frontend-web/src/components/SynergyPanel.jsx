/**
 * SynergyPanel — affiche les synergies d'un héros.
 * Cartes alliés avec score coloré, raison au survol.
 */
import { useState, useEffect } from "react";
import { getHeroSynergies } from "../api/heroes";
import TierBadge from "./TierBadge";

const ROLE_COLOR = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };

function scoreColor(score) {
  if (score >= 18) return "#FFD700";   // Or — synergie ultime
  if (score >= 15) return "#69db7c";   // Vert — forte
  if (score >= 12) return "#F4922B";   // Orange — bonne
  return "#aaa";                        // Gris — correcte
}

function scoreLabel(score) {
  if (score >= 18) return "Ultime";
  if (score >= 15) return "Forte";
  if (score >= 12) return "Bonne";
  return "Correcte";
}

function SynergyCard({ ally, isActive, onClick }) {
  const rc = ROLE_COLOR[ally.role] ?? "#aaa";
  const sc = scoreColor(ally.score);

  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center gap-1.5 p-2.5 text-left transition-all w-full"
      style={{
        background:  isActive ? "rgba(244,146,43,0.06)" : "rgba(11,18,33,0.6)",
        border:      `1px solid ${isActive ? sc : `${rc}30`}`,
        clipPath:    "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))",
        boxShadow:   isActive ? `0 0 12px ${sc}30` : "none",
      }}
    >
      {/* Portrait */}
      <div
        className="w-10 h-10 flex items-center justify-center overflow-hidden mx-auto"
        style={{
          background: "rgba(4,7,15,0.8)",
          border:     `1px solid ${rc}40`,
          clipPath:   "polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 4px 100%, 0 calc(100% - 4px))",
        }}
      >
        {ally.icon_url
          ? <img src={ally.icon_url} alt={ally.name} className="w-full h-full object-cover" />
          : <span className="text-xs font-bold text-white">{ally.name.slice(0, 2).toUpperCase()}</span>
        }
      </div>

      {/* Nom */}
      <p className="text-[11px] font-bold text-white text-center truncate w-full"
        style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.05em" }}>
        {ally.name}
      </p>

      {/* Score */}
      <span
        className="text-[10px] font-bold px-2 py-0.5"
        style={{
          color:      sc,
          background: `${sc}15`,
          border:     `1px solid ${sc}30`,
          clipPath:   "polygon(3px 0%, 100% 0%, calc(100% - 3px) 100%, 0% 100%)",
          fontFamily: "Rajdhani, sans-serif",
        }}
      >
        {scoreLabel(ally.score)}
      </span>
    </button>
  );
}

export default function SynergyPanel({ heroSlug }) {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(false);
  const [active,  setActive]  = useState(null);  // slug de l'allié actif

  useEffect(() => {
    if (!heroSlug) return;
    setLoading(true);
    setData(null);
    setActive(null);
    getHeroSynergies(heroSlug)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [heroSlug]);

  if (loading) return (
    <div className="text-center py-6 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
      Chargement des synergies…
    </div>
  );

  if (!data || data.synergies.length === 0) return (
    <div className="text-center py-6 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
      Aucune synergie définie pour ce héros.
    </div>
  );

  const activeAlly = data.synergies.find((a) => a.slug === active);

  return (
    <div className="space-y-4">
      {/* Grille d'alliés */}
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
        {data.synergies.map((ally) => (
          <SynergyCard
            key={ally.slug}
            ally={ally}
            isActive={active === ally.slug}
            onClick={() => setActive((v) => v === ally.slug ? null : ally.slug)}
          />
        ))}
      </div>

      {/* Panneau explication */}
      {activeAlly && (
        <div
          className="p-4 space-y-2"
          style={{
            background: "rgba(4,7,15,0.6)",
            border:     `1px solid ${scoreColor(activeAlly.score)}30`,
            clipPath:   "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))",
          }}
        >
          <div className="flex items-center gap-2">
            {/* Mini portrait */}
            <div
              className="w-7 h-7 flex items-center justify-center overflow-hidden shrink-0"
              style={{
                background: "rgba(4,7,15,0.8)",
                border:     `1px solid ${ROLE_COLOR[activeAlly.role] ?? "#aaa"}40`,
                clipPath:   "polygon(0 0, calc(100% - 3px) 0, 100% 3px, 100% 100%, 3px 100%, 0 calc(100% - 3px))",
              }}
            >
              {activeAlly.icon_url
                ? <img src={activeAlly.icon_url} alt={activeAlly.name} className="w-full h-full object-cover" />
                : <span className="text-[9px] font-bold text-white">{activeAlly.name.slice(0, 2).toUpperCase()}</span>
              }
            </div>
            <span
              className="font-bold text-sm"
              style={{ color: scoreColor(activeAlly.score), fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.08em" }}
            >
              {data.hero.name} + {activeAlly.name}
            </span>
            <TierBadge tier={activeAlly.tier} />
          </div>

          {activeAlly.reason ? (
            <p className="text-xs text-gray-300 leading-relaxed" style={{ fontFamily: "Barlow, sans-serif" }}>
              {activeAlly.reason}
            </p>
          ) : (
            <p className="text-xs text-gray-500 italic" style={{ fontFamily: "Barlow, sans-serif" }}>
              Synergie efficace dans le méta actuel.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
