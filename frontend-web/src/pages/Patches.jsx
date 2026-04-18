/**
 * Patches — historique des patch notes avec changements par héros.
 */
import { useState, useEffect } from "react";
import { getPatchNotes } from "../api/heroes";
import { LoadingSpinner, ErrorMessage } from "../components/LoadingSpinner";

// ─── Config ────────────────────────────────────────────────────────────────────
const TYPE_CFG = {
  buff:   { label: "Buff",   color: "#69db7c", bg: "rgba(105,219,124,0.08)", border: "rgba(105,219,124,0.25)", icon: "▲" },
  nerf:   { label: "Nerf",   color: "#FF4655", bg: "rgba(255,70,85,0.08)",   border: "rgba(255,70,85,0.25)",   icon: "▼" },
  rework: { label: "Rework", color: "#F4922B", bg: "rgba(244,146,43,0.08)", border: "rgba(244,146,43,0.25)",  icon: "◆" },
  fix:    { label: "Fix",    color: "#00C2FF", bg: "rgba(0,194,255,0.08)",  border: "rgba(0,194,255,0.25)",   icon: "●" },
};

const ROLE_COLOR = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };

// ─── Ligne de changement ───────────────────────────────────────────────────────
function ChangeRow({ change }) {
  const cfg  = TYPE_CFG[change.type] ?? TYPE_CFG.fix;
  const hero = change.hero;

  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-ow-border last:border-0">
      {/* Portrait héros */}
      <div
        className="overflow-hidden flex items-center justify-center shrink-0"
        style={{
          width: 36, height: 36,
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

      {/* Nom héros */}
      <div className="flex flex-col shrink-0 w-24">
        <span className="text-xs font-bold text-white truncate" style={{ fontFamily: "Rajdhani, sans-serif" }}>
          {hero?.name ?? change.hero_slug}
        </span>
        {hero?.role && (
          <span className="text-[9px] uppercase tracking-wider" style={{ color: ROLE_COLOR[hero.role], fontFamily: "Rajdhani, sans-serif" }}>
            {hero.role}
          </span>
        )}
      </div>

      {/* Badge type */}
      <span
        className="text-[10px] font-bold px-2 py-0.5 shrink-0 mt-0.5"
        style={{
          color:      cfg.color,
          background: cfg.bg,
          border:     `1px solid ${cfg.border}`,
          fontFamily: "Rajdhani, sans-serif",
          clipPath:   "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
        }}
      >
        {cfg.icon} {cfg.label}
      </span>

      {/* Texte */}
      <p className="text-xs text-gray-300 leading-relaxed flex-1" style={{ fontFamily: "Barlow, sans-serif" }}>
        {change.text}
      </p>
    </div>
  );
}

// ─── Carte patch ───────────────────────────────────────────────────────────────
function PatchCard({ patch, isActive, onClick }) {
  const buffCount   = patch.changes.filter((c) => c.type === "buff").length;
  const nerfCount   = patch.changes.filter((c) => c.type === "nerf").length;
  const reworkCount = patch.changes.filter((c) => c.type === "rework").length;

  return (
    <button
      onClick={onClick}
      className="w-full text-left px-4 py-3 transition-all"
      style={{
        background:   isActive ? "rgba(244,146,43,0.08)" : "transparent",
        borderLeft:   isActive ? "3px solid #F4922B"     : "3px solid transparent",
        borderBottom: "1px solid rgba(27,45,79,0.5)",
      }}
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-black text-sm text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
            {patch.version}
          </span>
          {patch.is_latest && (
            <span className="text-[9px] font-bold px-1.5 py-0.5 uppercase"
              style={{ background: "rgba(244,146,43,0.15)", color: "#F4922B", border: "1px solid rgba(244,146,43,0.3)",
                fontFamily: "Rajdhani, sans-serif", clipPath: "polygon(3px 0%, 100% 0%, calc(100% - 3px) 100%, 0% 100%)" }}>
              LIVE
            </span>
          )}
        </div>
        <span className="text-[10px] text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>
          {new Date(patch.date).toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric" })}
        </span>
      </div>

      <p className="text-[11px] text-gray-500 mt-0.5 truncate" style={{ fontFamily: "Barlow, sans-serif" }}>
        {patch.title || `Patch ${patch.version}`}
      </p>

      {/* Compteurs buff/nerf */}
      <div className="flex gap-2 mt-1.5">
        {buffCount   > 0 && <span className="text-[9px] font-bold" style={{ color: "#69db7c" }}>▲{buffCount}</span>}
        {nerfCount   > 0 && <span className="text-[9px] font-bold" style={{ color: "#FF4655" }}>▼{nerfCount}</span>}
        {reworkCount > 0 && <span className="text-[9px] font-bold" style={{ color: "#F4922B" }}>◆{reworkCount}</span>}
      </div>
    </button>
  );
}

// ─── Page principale ───────────────────────────────────────────────────────────
export default function Patches() {
  const [patches,  setPatches]  = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState(null);
  const [selected, setSelected] = useState(null);
  const [heroFilter, setHeroFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  useEffect(() => {
    getPatchNotes()
      .then((data) => {
        setPatches(data);
        if (data.length > 0) setSelected(data[0]);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const changes = selected?.changes_enriched ?? [];
  const filtered = changes.filter((c) => {
    const matchHero = heroFilter
      ? (c.hero?.name ?? "").toLowerCase().includes(heroFilter.toLowerCase())
      : true;
    const matchType = typeFilter === "all" ? true : c.type === typeFilter;
    return matchHero && matchType;
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 flex flex-col gap-6">

      {/* Titre */}
      <div>
        <h1 className="text-3xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.08em" }}>
          Patch Notes
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Historique des changements d'équilibrage par version.
        </p>
      </div>

      {loading && <LoadingSpinner text="Chargement des patches…" />}
      {error   && <ErrorMessage message={error} />}

      {!loading && !error && (
        <div className="flex gap-4" style={{ minHeight: "600px" }}>

          {/* Sidebar — liste des patches */}
          <div
            className="w-52 shrink-0 overflow-y-auto"
            style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))" }}
          >
            <div className="px-4 py-3 border-b border-ow-border">
              <span className="text-[10px] font-bold uppercase tracking-widest text-ow-accent" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                Versions
              </span>
            </div>
            {patches.map((p) => (
              <PatchCard
                key={p.version}
                patch={p}
                isActive={selected?.version === p.version}
                onClick={() => { setSelected(p); setHeroFilter(""); setTypeFilter("all"); }}
              />
            ))}
          </div>

          {/* Contenu principal */}
          <div className="flex-1 flex flex-col gap-4">
            {selected ? (
              <>
                {/* Header du patch */}
                <div
                  className="p-4"
                  style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
                >
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-2xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                          {selected.title || `Patch ${selected.version}`}
                        </span>
                        {selected.is_latest && (
                          <span className="text-[10px] font-bold px-2 py-0.5 uppercase"
                            style={{ background: "rgba(244,146,43,0.15)", color: "#F4922B", border: "1px solid rgba(244,146,43,0.3)",
                              fontFamily: "Rajdhani, sans-serif", clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)" }}>
                            LIVE
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-gray-500" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                        {new Date(selected.date).toLocaleDateString("fr-FR", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
                      </p>
                    </div>
                    <div className="flex gap-2">
                      {["buff","nerf","rework","fix"].map((t) => {
                        const count = changes.filter((c) => c.type === t).length;
                        if (!count) return null;
                        const cfg = TYPE_CFG[t];
                        return (
                          <span key={t} className="text-[10px] font-bold px-2 py-1"
                            style={{ color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`, fontFamily: "Rajdhani, sans-serif" }}>
                            {cfg.icon} {count} {cfg.label}{count > 1 ? "s" : ""}
                          </span>
                        );
                      })}
                    </div>
                  </div>

                  {selected.summary && (
                    <p className="text-xs text-gray-400 mt-3 leading-relaxed border-t border-ow-border pt-3" style={{ fontFamily: "Barlow, sans-serif" }}>
                      {selected.summary}
                    </p>
                  )}
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
                    {["all", "buff", "nerf", "rework", "fix"].map((t) => {
                      const cfg = t === "all" ? null : TYPE_CFG[t];
                      return (
                        <button key={t}
                          onClick={() => setTypeFilter(t)}
                          className="px-2.5 py-1 text-[10px] font-bold uppercase transition-all"
                          style={{
                            fontFamily: "Rajdhani, sans-serif",
                            background: typeFilter === t ? (cfg?.bg ?? "rgba(244,146,43,0.12)") : "transparent",
                            border:     `1px solid ${typeFilter === t ? (cfg?.border ?? "rgba(244,146,43,0.4)") : "rgba(27,45,79,0.8)"}`,
                            color:      typeFilter === t ? (cfg?.color ?? "#F4922B") : "#6b7280",
                            clipPath:   "polygon(3px 0%, 100% 0%, calc(100% - 3px) 100%, 0% 100%)",
                          }}
                        >
                          {t === "all" ? "Tous" : `${TYPE_CFG[t].icon} ${TYPE_CFG[t].label}`}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Liste des changements */}
                <div
                  className="flex-1 overflow-y-auto"
                  style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
                >
                  {filtered.length === 0 ? (
                    <div className="text-center py-10 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                      Aucun changement correspondant
                    </div>
                  ) : (
                    <div className="p-4">
                      {filtered.map((c, i) => <ChangeRow key={i} change={c} />)}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-center py-20 text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                Sélectionne un patch pour voir les changements
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
