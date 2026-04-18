/**
 * Matrix — grille 2D des matchups counter.
 * Lignes = héros joués, colonnes = héros ennemis.
 * Couleur par score : vert (favorable) → rouge (défavorable).
 */
import { useState, useRef } from "react";
import useHeroes from "../hooks/useHeroes";
import { LoadingSpinner, ErrorMessage } from "../components/LoadingSpinner";

// ─── Couleurs ──────────────────────────────────────────────────────────────────
function cellColor(score) {
  if (score === 0 || score === undefined) return { bg: "rgba(27,45,79,0.3)", text: "transparent" };
  if (score >= 15) return { bg: "rgba(105,219,124,0.35)", text: "#69db7c" };
  if (score >= 8)  return { bg: "rgba(105,219,124,0.18)", text: "#69db7c" };
  if (score >= 1)  return { bg: "rgba(105,219,124,0.08)", text: "#69db7c" };
  if (score <= -15)return { bg: "rgba(255,70,85,0.35)",   text: "#FF4655" };
  if (score <= -8) return { bg: "rgba(255,70,85,0.18)",   text: "#FF4655" };
  return           { bg: "rgba(255,70,85,0.08)",          text: "#FF4655" };
}

const ROLE_COLOR = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };
const ROLES      = ["tank", "dps", "support"];
const ROLE_LABEL = { tank: "Tank", dps: "DPS", support: "Support" };

// ─── Tooltip ───────────────────────────────────────────────────────────────────
function Tooltip({ hero, enemy, score, visible, x, y }) {
  if (!visible || !hero || !enemy) return null;
  const { text } = cellColor(score);
  const label = score > 0 ? `+${score} favorable` : score < 0 ? `${score} défavorable` : "neutre";

  return (
    <div
      className="fixed z-[200] pointer-events-none px-3 py-2 text-xs"
      style={{
        left: x + 12,
        top:  y - 8,
        background: "#0B1221",
        border: `1px solid ${text === "transparent" ? "rgba(27,45,79,0.8)" : text}40`,
        clipPath: "polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px))",
        boxShadow: `0 4px 20px rgba(0,0,0,0.6)`,
        minWidth: "140px",
        maxWidth: "220px",
      }}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <span className="font-bold text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
          {hero.name}
        </span>
        <span className="text-gray-500">vs</span>
        <span className="font-bold text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
          {enemy.name}
        </span>
      </div>
      <span
        className="font-bold text-[11px]"
        style={{ color: text === "transparent" ? "#6b7280" : text, fontFamily: "Rajdhani, sans-serif" }}
      >
        {label}
      </span>
    </div>
  );
}

// ─── Filtre de rôle ────────────────────────────────────────────────────────────
function RoleFilter({ value, onChange, label }) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-[10px] uppercase tracking-widest text-gray-500" style={{ fontFamily: "Rajdhani, sans-serif" }}>
        {label}
      </span>
      <div className="flex gap-1">
        <button
          onClick={() => onChange(null)}
          className="px-2.5 py-1 text-xs font-bold transition-all"
          style={{
            fontFamily: "Rajdhani, sans-serif",
            background: value === null ? "rgba(244,146,43,0.12)" : "rgba(11,18,33,0.6)",
            border:     `1px solid ${value === null ? "#F4922B" : "rgba(27,45,79,0.8)"}`,
            color:      value === null ? "#F4922B" : "#6b7280",
            clipPath:   "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
          }}
        >
          Tous
        </button>
        {ROLES.map((r) => (
          <button
            key={r}
            onClick={() => onChange(r)}
            className="px-2.5 py-1 text-xs font-bold transition-all"
            style={{
              fontFamily: "Rajdhani, sans-serif",
              background: value === r ? `${ROLE_COLOR[r]}15` : "rgba(11,18,33,0.6)",
              border:     `1px solid ${value === r ? ROLE_COLOR[r] : "rgba(27,45,79,0.8)"}`,
              color:      value === r ? ROLE_COLOR[r] : "#6b7280",
              clipPath:   "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
            }}
          >
            {ROLE_LABEL[r]}
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Page principale ───────────────────────────────────────────────────────────
export default function Matrix() {
  const { heroes, loading, error } = useHeroes();
  const [rowRole, setRowRole]   = useState(null);   // héros joués
  const [colRole, setColRole]   = useState(null);   // héros ennemis
  const [tooltip, setTooltip]   = useState({ visible: false, hero: null, enemy: null, score: 0, x: 0, y: 0 });
  const containerRef            = useRef(null);

  if (loading) return <LoadingSpinner text="Chargement des héros…" />;
  if (error)   return <ErrorMessage message={error} />;

  const rowHeroes = rowRole ? heroes.filter((h) => h.role === rowRole) : heroes;
  const colHeroes = colRole ? heroes.filter((h) => h.role === colRole) : heroes;

  // Regroupe les colonnes par rôle pour l'en-tête
  const colGroups = ROLES
    .map((r) => ({ role: r, cols: colHeroes.filter((h) => h.role === r) }))
    .filter((g) => g.cols.length > 0);

  const handleMouseMove = (e, hero, enemy, score) => {
    setTooltip({ visible: true, hero, enemy, score, x: e.clientX, y: e.clientY });
  };
  const handleMouseLeave = () => setTooltip((t) => ({ ...t, visible: false }));

  const CELL = 28; // taille d'une cellule en px

  return (
    <div className="max-w-full mx-auto flex flex-col gap-6 px-4 py-8">

      {/* Titre */}
      <div>
        <h1 className="text-3xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.08em" }}>
          Matchup Matrix
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Scores de counter entre héros — vert = favorable, rouge = défavorable.
        </p>
      </div>

      {/* Filtres */}
      <div
        className="flex flex-wrap gap-6 p-4"
        style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
      >
        <RoleFilter label="Héros joués (lignes)"   value={rowRole} onChange={setRowRole} />
        <RoleFilter label="Héros ennemis (colonnes)" value={colRole} onChange={setColRole} />

        {/* Légende */}
        <div className="flex flex-col gap-1.5 ml-auto">
          <span className="text-[10px] uppercase tracking-widest text-gray-500" style={{ fontFamily: "Rajdhani, sans-serif" }}>
            Légende
          </span>
          <div className="flex items-center gap-2">
            {[
              { bg: "rgba(105,219,124,0.35)", label: "Fort (+15)", text: "#69db7c" },
              { bg: "rgba(105,219,124,0.18)", label: "Bon (+8)",   text: "#69db7c" },
              { bg: "rgba(27,45,79,0.3)",     label: "Neutre",     text: "#6b7280" },
              { bg: "rgba(255,70,85,0.18)",   label: "Faible (-8)", text: "#FF4655" },
              { bg: "rgba(255,70,85,0.35)",   label: "Mauvais (-15)", text: "#FF4655" },
            ].map(({ bg, label, text }) => (
              <div key={label} className="flex items-center gap-1">
                <div className="w-4 h-4 shrink-0" style={{ background: bg, border: `1px solid ${text}30` }} />
                <span className="text-[10px] text-gray-500 whitespace-nowrap" style={{ fontFamily: "Rajdhani, sans-serif" }}>{label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compteur */}
      <div className="text-xs text-gray-600" style={{ fontFamily: "Rajdhani, sans-serif" }}>
        {rowHeroes.length} × {colHeroes.length} = {rowHeroes.length * colHeroes.length} cellules
      </div>

      {/* Matrice */}
      <div className="overflow-auto" ref={containerRef}>
        <table className="border-collapse" style={{ minWidth: "max-content" }}>
          <thead>
            {/* Ligne de groupes de rôles */}
            <tr>
              {/* Coin vide */}
              <th className="sticky left-0 z-20" style={{ background: "#04070F", minWidth: "120px" }} />
              {colGroups.map(({ role, cols }) => (
                <th
                  key={role}
                  colSpan={cols.length}
                  className="text-center text-[10px] font-bold uppercase tracking-widest pb-1 px-1"
                  style={{
                    color:       ROLE_COLOR[role],
                    borderBottom: `2px solid ${ROLE_COLOR[role]}40`,
                    fontFamily:  "Rajdhani, sans-serif",
                  }}
                >
                  {ROLE_LABEL[role]}
                </th>
              ))}
            </tr>

            {/* Noms des héros ennemis (colonnes) — portrait vertical */}
            <tr>
              <th className="sticky left-0 z-20 text-left text-[10px] text-gray-600 pb-1 pr-2 uppercase tracking-wider"
                style={{ background: "#04070F", fontFamily: "Rajdhani, sans-serif" }}>
                Héros ↓ / Ennemis →
              </th>
              {colHeroes.map((enemy) => (
                <th
                  key={enemy.slug}
                  title={enemy.name}
                  className="p-0.5"
                  style={{ minWidth: `${CELL}px`, maxWidth: `${CELL}px` }}
                >
                  <div className="flex flex-col items-center gap-0.5">
                    <div
                      className="overflow-hidden flex items-center justify-center"
                      style={{
                        width:  CELL - 2,
                        height: CELL - 2,
                        background:  "rgba(4,7,15,0.8)",
                        border:      `1px solid ${ROLE_COLOR[enemy.role]}30`,
                        clipPath:    "polygon(0 0, calc(100% - 3px) 0, 100% 3px, 100% 100%, 3px 100%, 0 calc(100% - 3px))",
                      }}
                    >
                      {enemy.icon_url
                        ? <img src={enemy.icon_url} alt={enemy.name} style={{ width: CELL - 2, height: CELL - 2, objectFit: "cover" }} />
                        : <span style={{ fontSize: 8, color: "#fff", fontWeight: "bold" }}>{enemy.name.slice(0, 2)}</span>
                      }
                    </div>
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rowHeroes.map((hero, ri) => {
              // Séparateur de groupe de rôle
              const prevRole = ri > 0 ? rowHeroes[ri - 1].role : null;
              const showSep  = prevRole && prevRole !== hero.role;

              return (
                <>
                  {showSep && (
                    <tr key={`sep-${hero.slug}`}>
                      <td colSpan={colHeroes.length + 1} style={{ height: "4px", background: "transparent" }} />
                    </tr>
                  )}
                  <tr key={hero.slug}>
                    {/* Nom du héros en ligne (sticky) */}
                    <td
                      className="sticky left-0 z-10 pr-2 py-0.5"
                      style={{ background: "#04070F" }}
                    >
                      <div className="flex items-center gap-1.5">
                        <div
                          className="overflow-hidden flex items-center justify-center shrink-0"
                          style={{
                            width: 20, height: 20,
                            background: "rgba(4,7,15,0.8)",
                            border: `1px solid ${ROLE_COLOR[hero.role]}30`,
                            clipPath: "polygon(0 0, calc(100% - 2px) 0, 100% 2px, 100% 100%, 2px 100%, 0 calc(100% - 2px))",
                          }}
                        >
                          {hero.icon_url
                            ? <img src={hero.icon_url} alt={hero.name} style={{ width: 20, height: 20, objectFit: "cover" }} />
                            : <span style={{ fontSize: 7, color: "#fff", fontWeight: "bold" }}>{hero.name.slice(0, 2)}</span>
                          }
                        </div>
                        <span
                          className="text-xs font-bold truncate"
                          style={{
                            maxWidth: "80px",
                            color: ROLE_COLOR[hero.role],
                            fontFamily: "Rajdhani, sans-serif",
                            letterSpacing: "0.04em",
                          }}
                        >
                          {hero.name}
                        </span>
                      </div>
                    </td>

                    {/* Cellules */}
                    {colHeroes.map((enemy) => {
                      const score = hero.counters?.[enemy.slug] ?? 0;
                      const { bg, text } = cellColor(score);
                      const isSelf = hero.slug === enemy.slug;

                      return (
                        <td
                          key={enemy.slug}
                          onMouseMove={(e) => !isSelf && handleMouseMove(e, hero, enemy, score)}
                          onMouseLeave={handleMouseLeave}
                          style={{
                            width:      CELL,
                            height:     CELL,
                            background: isSelf ? "rgba(244,146,43,0.08)" : bg,
                            border:     "1px solid rgba(27,45,79,0.2)",
                            cursor:     isSelf ? "default" : "crosshair",
                            textAlign:  "center",
                            verticalAlign: "middle",
                            transition: "background 0.1s",
                          }}
                        >
                          {!isSelf && score !== 0 && (
                            <span
                              style={{
                                fontSize:   9,
                                fontWeight: "bold",
                                color:      text,
                                fontFamily: "Rajdhani, sans-serif",
                                lineHeight: 1,
                              }}
                            >
                              {score > 0 ? `+${score}` : score}
                            </span>
                          )}
                          {isSelf && (
                            <span style={{ fontSize: 9, color: "#F4922B", opacity: 0.5 }}>—</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                </>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Tooltip global */}
      <Tooltip {...tooltip} />
    </div>
  );
}
