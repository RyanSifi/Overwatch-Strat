/**
 * Meta — Top comps du méta actuel, classées par style.
 */
import { useState, useEffect } from "react";
import { getMetaComps }  from "../api/heroes";
import TierBadge         from "../components/TierBadge";
import { LoadingSpinner, ErrorMessage } from "../components/LoadingSpinner";

// ─── Config ────────────────────────────────────────────────────────────────────
const STYLE_CFG = {
  dive:   { label: "Dive",   color: "#a855f7", bg: "rgba(168,85,247,0.08)",  border: "rgba(168,85,247,0.25)",  dot: "bg-purple-500" },
  brawl:  { label: "Brawl",  color: "#ef4444", bg: "rgba(239,68,68,0.08)",   border: "rgba(239,68,68,0.25)",   dot: "bg-red-500"    },
  poke:   { label: "Poke",   color: "#eab308", bg: "rgba(234,179,8,0.08)",   border: "rgba(234,179,8,0.25)",   dot: "bg-yellow-500" },
  rush:   { label: "Rush",   color: "#F4922B", bg: "rgba(244,146,43,0.08)",  border: "rgba(244,146,43,0.25)",  dot: "bg-orange-500" },
  hybrid: { label: "Hybrid", color: "#00C2FF", bg: "rgba(0,194,255,0.08)",   border: "rgba(0,194,255,0.25)",   dot: "bg-cyan-500"   },
};

const ROLE_COLOR = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };
const STYLES     = ["all", "dive", "brawl", "poke", "rush", "hybrid"];

// ─── Carte comp ────────────────────────────────────────────────────────────────
function CompCard({ comp }) {
  const cfg = STYLE_CFG[comp.style] ?? STYLE_CFG.hybrid;

  return (
    <div
      className="flex flex-col gap-4 p-5 transition-all hover:scale-[1.01]"
      style={{
        background: "#0B1221",
        border:     `1px solid ${comp.is_featured ? cfg.border : "rgba(27,45,79,0.8)"}`,
        clipPath:   "polygon(0 0, calc(100% - 12px) 0, 100% 12px, 100% 100%, 12px 100%, 0 calc(100% - 12px))",
        boxShadow:  comp.is_featured ? `0 0 20px ${cfg.color}15` : "none",
      }}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            {comp.is_featured && (
              <span className="text-[9px] font-bold px-2 py-0.5 uppercase tracking-widest"
                style={{ background: `${cfg.color}20`, color: cfg.color, border: `1px solid ${cfg.border}`, fontFamily: "Rajdhani, sans-serif",
                  clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)" }}>
                TOP META
              </span>
            )}
            <span
              className="text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider"
              style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}`, fontFamily: "Rajdhani, sans-serif",
                clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)" }}
            >
              {cfg.label}
            </span>
          </div>
          <h3 className="text-base font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.06em" }}>
            {comp.name}
          </h3>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <TierBadge tier={comp.tier} />
          {comp.win_rate > 0 && (
            <span className="text-[11px] font-bold px-2 py-0.5"
              style={{ color: comp.win_rate >= 53 ? "#69db7c" : comp.win_rate >= 50 ? "#F4922B" : "#FF4655",
                background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
                fontFamily: "Rajdhani, sans-serif" }}>
              {comp.win_rate.toFixed(1)}% WR
            </span>
          )}
        </div>
      </div>

      {/* Portraits héros */}
      <div className="flex gap-2">
        {comp.heroes_data.map((hero) => (
          <div key={hero.slug} className="flex flex-col items-center gap-1">
            <div
              className="overflow-hidden flex items-center justify-center"
              style={{
                width: 44, height: 44,
                background: "rgba(4,7,15,0.8)",
                border: `2px solid ${ROLE_COLOR[hero.role] ?? "#444"}`,
                clipPath: "polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 5px 100%, 0 calc(100% - 5px))",
                boxShadow: `0 0 8px ${ROLE_COLOR[hero.role] ?? "#444"}30`,
              }}
            >
              {hero.icon_url
                ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover" />
                : <span className="text-xs font-bold text-white">{hero.name.slice(0,2)}</span>
              }
            </div>
            <span className="text-[9px] text-gray-500 truncate" style={{ maxWidth: 44, fontFamily: "Rajdhani, sans-serif" }}>
              {hero.name.split(":")[0]}
            </span>
          </div>
        ))}
      </div>

      {/* Description */}
      {comp.description && (
        <p className="text-xs text-gray-400 leading-relaxed border-t border-ow-border pt-3"
          style={{ fontFamily: "Barlow, sans-serif" }}>
          {comp.description}
        </p>
      )}
    </div>
  );
}

// ─── Page principale ───────────────────────────────────────────────────────────
export default function Meta() {
  const [comps,   setComps]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);
  const [filter,  setFilter]  = useState("all");

  useEffect(() => {
    getMetaComps()
      .then(setComps)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === "all" ? comps : comps.filter((c) => c.style === filter);
  const featured = filtered.filter((c) => c.is_featured);
  const others   = filtered.filter((c) => !c.is_featured);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 flex flex-col gap-6">

      {/* Titre */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.08em" }}>
            Méta du moment
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Meilleures compositions du patch actuel — classées par style et win rate.
          </p>
        </div>
        <span className="text-xs px-3 py-1.5 font-bold uppercase tracking-widest"
          style={{ background: "rgba(244,146,43,0.1)", border: "1px solid rgba(244,146,43,0.3)", color: "#F4922B",
            fontFamily: "Rajdhani, sans-serif", clipPath: "polygon(6px 0%, 100% 0%, calc(100% - 6px) 100%, 0% 100%)" }}>
          Saison 14
        </span>
      </div>

      {/* Filtres style */}
      <div className="flex gap-1.5 flex-wrap">
        {STYLES.map((s) => {
          const cfg = s === "all" ? null : STYLE_CFG[s];
          const active = filter === s;
          return (
            <button
              key={s}
              onClick={() => setFilter(s)}
              className="px-3 py-1.5 text-xs font-bold uppercase tracking-wider transition-all"
              style={{
                fontFamily:  "Rajdhani, sans-serif",
                background:  active ? (cfg ? cfg.bg : "rgba(244,146,43,0.12)") : "rgba(11,18,33,0.6)",
                border:      `1px solid ${active ? (cfg ? cfg.border : "rgba(244,146,43,0.4)") : "rgba(27,45,79,0.8)"}`,
                color:       active ? (cfg ? cfg.color : "#F4922B") : "#6b7280",
                clipPath:    "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
              }}
            >
              {s === "all" ? "Tous" : STYLE_CFG[s].label}
            </button>
          );
        })}
      </div>

      {loading && <LoadingSpinner text="Chargement du méta…" />}
      {error   && <ErrorMessage message={error} />}

      {!loading && !error && (
        <>
          {/* TOP META */}
          {featured.length > 0 && (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="h-px flex-1" style={{ background: "rgba(244,146,43,0.2)" }} />
                <span className="text-[10px] font-bold uppercase tracking-widest text-ow-accent" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                  ⭐ Top méta
                </span>
                <div className="h-px flex-1" style={{ background: "rgba(244,146,43,0.2)" }} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {featured.map((c) => <CompCard key={c.id} comp={c} />)}
              </div>
            </div>
          )}

          {/* Autres comps */}
          {others.length > 0 && (
            <div className="flex flex-col gap-3">
              {featured.length > 0 && (
                <div className="flex items-center gap-3">
                  <div className="h-px flex-1 bg-ow-border" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-gray-500" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                    Autres compositions viables
                  </span>
                  <div className="h-px flex-1 bg-ow-border" />
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {others.map((c) => <CompCard key={c.id} comp={c} />)}
              </div>
            </div>
          )}

          {filtered.length === 0 && (
            <div className="text-center py-12 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              Aucune composition pour ce style.
            </div>
          )}
        </>
      )}
    </div>
  );
}
