/**
 * Patches — patch notes du patch actuel uniquement.
 */
import { useState, useEffect } from "react";
import { getLatestPatch } from "../api/heroes";
import { LoadingSpinner, ErrorMessage } from "../components/LoadingSpinner";

const TYPE_CFG = {
  buff:   { label: "Buff",   color: "#69db7c", bg: "rgba(105,219,124,0.08)", border: "rgba(105,219,124,0.25)", icon: "▲" },
  nerf:   { label: "Nerf",   color: "#FF4655", bg: "rgba(255,70,85,0.08)",   border: "rgba(255,70,85,0.25)",   icon: "▼" },
  rework: { label: "Rework", color: "#F4922B", bg: "rgba(244,146,43,0.08)", border: "rgba(244,146,43,0.25)",  icon: "◆" },
  fix:    { label: "Fix",    color: "#00C2FF", bg: "rgba(0,194,255,0.08)",  border: "rgba(0,194,255,0.25)",   icon: "●" },
};

const ROLE_COLOR = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };

function ChangeRow({ change }) {
  const cfg  = TYPE_CFG[change.type] ?? TYPE_CFG.fix;
  const hero = change.hero;

  return (
    <div className="flex items-start gap-3 py-3 border-b border-ow-border last:border-0">
      <div
        className="overflow-hidden flex items-center justify-center shrink-0"
        style={{
          width: 38, height: 38,
          background: "rgba(4,7,15,0.8)",
          border: `1px solid ${ROLE_COLOR[hero?.role] ?? "#444"}40`,
          clipPath: "polygon(0 0, calc(100% - 4px) 0, 100% 4px, 100% 100%, 4px 100%, 0 calc(100% - 4px))",
        }}
      >
        {hero?.icon_url
          ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover" />
          : <span className="text-[10px] font-bold text-white">{(hero?.name ?? "?").slice(0,2)}</span>
        }
      </div>

      <div className="flex flex-col shrink-0 w-24 justify-center">
        <span className="text-xs font-bold text-white truncate" style={{ fontFamily: "Rajdhani, sans-serif" }}>
          {hero?.name ?? change.hero_slug}
        </span>
        {hero?.role && (
          <span className="text-[9px] uppercase tracking-wider" style={{ color: ROLE_COLOR[hero.role], fontFamily: "Rajdhani, sans-serif" }}>
            {hero.role}
          </span>
        )}
      </div>

      <span
        className="text-[10px] font-bold px-2 py-0.5 shrink-0 mt-0.5"
        style={{
          color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`,
          fontFamily: "Rajdhani, sans-serif",
          clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
        }}
      >
        {cfg.icon} {cfg.label}
      </span>

      <p className="text-xs text-gray-300 leading-relaxed flex-1" style={{ fontFamily: "Barlow, sans-serif" }}>
        {change.text}
      </p>
    </div>
  );
}

export default function Patches() {
  const [patch,      setPatch]      = useState(null);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);
  const [heroFilter, setHeroFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    getLatestPatch()
      .then(setPatch)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const changes = patch?.changes_enriched ?? [];
  const filtered = changes.filter((c) => {
    const matchHero = heroFilter ? (c.hero?.name ?? "").toLowerCase().includes(heroFilter.toLowerCase()) : true;
    const matchType = typeFilter === "all" ? true : c.type === typeFilter;
    return matchHero && matchType;
  });

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 flex flex-col gap-6">

      {/* Titre */}
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-3xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.08em" }}>
            Patch Notes
          </h1>
          <p className="text-gray-400 text-sm mt-1">Changements d'équilibrage du patch actuel.</p>
        </div>
        {patch && (
          <div className="flex items-center gap-2">
            <span className="text-xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              {patch.version}
            </span>
            <span className="text-[10px] font-bold px-2 py-0.5 uppercase"
              style={{ background: "rgba(244,146,43,0.15)", color: "#F4922B", border: "1px solid rgba(244,146,43,0.3)",
                fontFamily: "Rajdhani, sans-serif", clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)" }}>
              LIVE
            </span>
            <span className="text-xs text-gray-500" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              {patch.date && new Date(patch.date).toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}
            </span>
          </div>
        )}
      </div>

      {loading && <LoadingSpinner text="Chargement du patch…" />}
      {error   && <ErrorMessage message={error} />}

      {patch && !loading && (
        <>
          {/* Résumé */}
          {patch.summary && (
            <div className="px-4 py-3"
              style={{ background: "rgba(244,146,43,0.05)", border: "1px solid rgba(244,146,43,0.2)",
                clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}>
              <p className="text-sm text-gray-300 leading-relaxed" style={{ fontFamily: "Barlow, sans-serif" }}>
                {patch.summary}
              </p>
            </div>
          )}

          {/* Compteurs */}
          <div className="flex gap-2 flex-wrap">
            {["buff","nerf","rework","fix"].map((t) => {
              const count = changes.filter((c) => c.type === t).length;
              if (!count) return null;
              const cfg = TYPE_CFG[t];
              return (
                <span key={t} className="text-[11px] font-bold px-3 py-1"
                  style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`,
                    fontFamily: "Rajdhani, sans-serif" }}>
                  {cfg.icon} {count} {cfg.label}{count > 1 ? "s" : ""}
                </span>
              );
            })}
          </div>

          {/* Filtres */}
          <div className="flex gap-3 flex-wrap items-center">
            <input
              type="text"
              placeholder="Filtrer par héros…"
              value={heroFilter}
              onChange={(e) => setHeroFilter(e.target.value)}
              className="bg-ow-surface border border-ow-border rounded-lg px-3 py-1.5 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-ow-accent transition-colors"
              style={{ minWidth: "160px" }}
            />
            <div className="flex gap-1">
              {["all","buff","nerf","rework","fix"].map((t) => {
                const cfg = t === "all" ? null : TYPE_CFG[t];
                const active = typeFilter === t;
                return (
                  <button key={t} onClick={() => setTypeFilter(t)}
                    className="px-2.5 py-1 text-[10px] font-bold uppercase transition-all"
                    style={{
                      fontFamily: "Rajdhani, sans-serif",
                      background: active ? (cfg?.bg ?? "rgba(244,146,43,0.12)") : "transparent",
                      border:     `1px solid ${active ? (cfg?.border ?? "rgba(244,146,43,0.4)") : "rgba(27,45,79,0.8)"}`,
                      color:      active ? (cfg?.color ?? "#F4922B") : "#6b7280",
                      clipPath:   "polygon(3px 0%, 100% 0%, calc(100% - 3px) 100%, 0% 100%)",
                    }}
                  >
                    {t === "all" ? "Tous" : `${TYPE_CFG[t].icon} ${TYPE_CFG[t].label}`}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Liste */}
          <div
            style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)",
              clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
          >
            {filtered.length === 0
              ? <div className="text-center py-10 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>Aucun changement correspondant</div>
              : <div className="p-4">{filtered.map((c, i) => <ChangeRow key={i} change={c} />)}</div>
            }
          </div>
        </>
      )}
    </div>
  );
}
