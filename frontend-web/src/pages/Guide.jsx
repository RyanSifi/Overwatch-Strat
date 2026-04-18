/**
 * Guide — stratégies par map et par phase.
 */
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import useMaps       from "../hooks/useMaps";
import { getMapGuide } from "../api/maps";
import MapSelector   from "../components/MapSelector";
import TierBadge     from "../components/TierBadge";
import FavoriteButton from "../components/FavoriteButton";
import { LoadingSpinner, ErrorMessage, EmptyState } from "../components/LoadingSpinner";

// ─── Config style ──────────────────────────────────────────────────────────────
const STYLE_CONFIG = {
  dive:  { label: "Dive",  bg: "bg-purple-500/10", border: "border-purple-500/40", text: "text-purple-300", dot: "bg-purple-400" },
  brawl: { label: "Brawl", bg: "bg-red-500/10",    border: "border-red-500/40",    text: "text-red-300",    dot: "bg-red-400"    },
  poke:  { label: "Poke",  bg: "bg-yellow-500/10", border: "border-yellow-500/40", text: "text-yellow-300", dot: "bg-yellow-400" },
};

const ROLE_CONFIG = {
  tank:    { label: "Tank",    accent: "text-blue-400",   border: "border-l-blue-400",   header: "bg-blue-400/10"   },
  dps:     { label: "DPS",     accent: "text-orange-400", border: "border-l-orange-400", header: "bg-orange-400/10" },
  support: { label: "Support", accent: "text-green-400",  border: "border-l-green-400",  header: "bg-green-400/10"  },
};

const ROLE_EMOJI = { tank: "🛡", dps: "⚔", support: "💚" };

const MAP_TYPE_LABEL = {
  escort:     "Escorte",
  control:    "Contrôle",
  hybrid:     "Hybride",
  push:       "Push",
  flashpoint: "Flashpoint",
  clash:      "Clash",
};

const MAP_TYPE_COLOR = {
  escort:     "bg-blue-500/20 text-blue-300 border-blue-500/40",
  control:    "bg-purple-500/20 text-purple-300 border-purple-500/40",
  hybrid:     "bg-orange-500/20 text-orange-300 border-orange-500/40",
  push:       "bg-green-500/20 text-green-300 border-green-500/40",
  flashpoint: "bg-red-500/20 text-red-300 border-red-500/40",
  clash:      "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
};

// ─── Hero pick card ────────────────────────────────────────────────────────────
function HeroPickCard({ hero }) {
  if (!hero) return null;

  const roleColor = {
    tank:    "border-blue-400/50 bg-blue-400/5",
    dps:     "border-orange-400/50 bg-orange-400/5",
    support: "border-green-400/50 bg-green-400/5",
  }[hero.role] ?? "border-ow-border bg-ow-surface";

  return (
    <div className={`relative flex flex-col items-center gap-1.5 p-2.5 rounded-xl border ${roleColor} transition-all hover:scale-105`}>
      {/* Badge NEW */}
      {hero.is_new && (
        <span className="absolute -top-1.5 -right-1.5 bg-ow-accent text-white text-[8px] font-bold px-1.5 py-0.5 rounded-full">
          NEW
        </span>
      )}

      {/* Portrait */}
      <div className="w-12 h-12 rounded-lg bg-ow-border/40 overflow-hidden flex items-center justify-center flex-shrink-0">
        {hero.icon_url
          ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover" />
          : <span className="text-sm font-bold text-white">{hero.name.slice(0, 2).toUpperCase()}</span>
        }
      </div>

      {/* Nom */}
      <p className="text-[11px] font-semibold text-white text-center leading-tight truncate w-full">
        {hero.name}
      </p>

      {/* Tier */}
      {hero.tier && <TierBadge tier={hero.tier} />}
    </div>
  );
}

// ─── Colonne rôle ──────────────────────────────────────────────────────────────
function RoleColumn({ role, heroes = [] }) {
  const cfg = ROLE_CONFIG[role] ?? { label: role, accent: "text-gray-400", border: "border-l-gray-400", header: "bg-gray-400/10" };

  return (
    <div className={`flex flex-col rounded-xl border border-ow-border overflow-hidden`}>
      {/* Header */}
      <div className={`flex items-center gap-2 px-3 py-2 ${cfg.header} border-b border-ow-border`}>
        <span>{ROLE_EMOJI[role] ?? "?"}</span>
        <span className={`text-xs font-bold uppercase tracking-wider ${cfg.accent}`}>
          {cfg.label}
        </span>
        <span className="ml-auto text-xs text-gray-600 font-medium">{heroes.length}</span>
      </div>

      {/* Grille de picks */}
      <div className="p-3">
        {heroes.length > 0 ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {heroes.map((hero) => (
              <HeroPickCard key={hero.slug} hero={hero} />
            ))}
          </div>
        ) : (
          <p className="text-xs text-gray-600 italic py-2 text-center">Aucun héros</p>
        )}
      </div>
    </div>
  );
}

// ─── Phase card ────────────────────────────────────────────────────────────────
function PhaseCard({ phase, index, total }) {
  const { tank = [], dps = [], support = [] } = phase.recommended ?? {};
  const styleCfg = STYLE_CONFIG[phase.style?.toLowerCase()] ?? {
    label: phase.style ?? "—",
    bg: "bg-gray-500/10", border: "border-gray-500/40", text: "text-gray-300", dot: "bg-gray-400",
  };

  return (
    <div className="bg-ow-surface border border-ow-border rounded-2xl overflow-hidden">
      {/* Header de la phase */}
      <div className="flex flex-wrap items-center gap-3 px-5 py-4 border-b border-ow-border">
        {/* Numéro */}
        <div className="flex items-center gap-2.5 flex-1 min-w-0">
          <span className="w-8 h-8 flex items-center justify-center rounded-full bg-ow-accent/20 text-ow-accent text-sm font-black shrink-0">
            {index + 1}
          </span>
          <div className="min-w-0">
            <h3 className="font-bold text-white text-base truncate">{phase.name}</h3>
            <p className="text-xs text-gray-500">Phase {index + 1} / {total}</p>
          </div>
        </div>

        {/* Badge style */}
        {phase.style && (
          <span className={`inline-flex items-center gap-1.5 border rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wide ${styleCfg.bg} ${styleCfg.border} ${styleCfg.text}`}>
            <span className={`w-1.5 h-1.5 rounded-full ${styleCfg.dot}`} />
            {styleCfg.label}
          </span>
        )}
      </div>

      {/* Notes */}
      {phase.notes && (
        <div className={`mx-4 mt-4 px-4 py-3 rounded-xl border ${styleCfg.bg} ${styleCfg.border}`}>
          <p className={`text-sm leading-relaxed ${styleCfg.text}`}>
            {phase.notes}
          </p>
        </div>
      )}

      {/* Picks par rôle */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-4">
        <RoleColumn role="tank"    heroes={tank}    />
        <RoleColumn role="dps"     heroes={dps}     />
        <RoleColumn role="support" heroes={support} />
      </div>
    </div>
  );
}

// ─── Page principale ───────────────────────────────────────────────────────────
export default function Guide() {
  const { maps, loading: mapsLoading, error: mapsError } = useMaps();
  const [searchParams] = useSearchParams();

  const [selectedSlug, setSelectedSlug] = useState(() => searchParams.get("map") || null);
  const [guide,        setGuide]        = useState(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [guideError,   setGuideError]   = useState(null);
  const [activePhase,  setActivePhase]  = useState(0);

  useEffect(() => {
    if (!selectedSlug) { setGuide(null); setGuideError(null); return; }
    setGuideLoading(true);
    setGuideError(null);
    setGuide(null);
    setActivePhase(0);
    getMapGuide(selectedSlug)
      .then(setGuide)
      .catch((e) => setGuideError(e.response?.data?.detail ?? e.message))
      .finally(()  => setGuideLoading(false));
  }, [selectedSlug]);

  const phases = guide?.phases ?? [];
  const mapInfo = guide?.map;

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6 px-4 py-8">

      {/* Titre */}
      <div>
        <h1 className="text-3xl font-black text-white">Guide des maps</h1>
        <p className="text-gray-400 text-sm mt-1">
          Stratégies et compositions recommandées, phase par phase.
        </p>
      </div>

      {/* Sélecteur de map */}
      <div className="bg-ow-surface border border-ow-border rounded-xl p-4 flex flex-wrap items-center gap-4">
        <span className="text-sm text-gray-400 font-medium shrink-0">Map :</span>

        {mapsLoading && <LoadingSpinner text="Chargement…" />}
        {mapsError   && <ErrorMessage message={mapsError} />}

        {!mapsLoading && !mapsError && (
          <MapSelector maps={maps} value={selectedSlug} onChange={setSelectedSlug} showType />
        )}

        {/* Infos de la map sélectionnée */}
        {mapInfo && (
          <div className="ml-auto flex items-center gap-2">
            <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${MAP_TYPE_COLOR[mapInfo.map_type] ?? "bg-gray-500/20 text-gray-400 border-gray-500/40"}`}>
              {MAP_TYPE_LABEL[mapInfo.map_type] ?? mapInfo.map_type}
            </span>
            <span className="text-xs text-gray-500">{phases.length} phase{phases.length > 1 ? "s" : ""}</span>
            <FavoriteButton type="map" slug={selectedSlug} size="md" />
          </div>
        )}
      </div>

      {/* État initial */}
      {!selectedSlug && (
        <EmptyState icon="🗺" message="Sélectionne une map pour afficher son guide stratégique." />
      )}

      {selectedSlug && guideLoading && <LoadingSpinner text="Chargement du guide…" />}
      {selectedSlug && guideError   && <ErrorMessage message={guideError} />}

      {/* Navigation des phases (tabs) */}
      {phases.length > 1 && (
        <div className="flex gap-2 flex-wrap">
          {phases.map((phase, i) => {
            const styleCfg = STYLE_CONFIG[phase.style?.toLowerCase()];
            const isActive = activePhase === i;
            return (
              <button
                key={i}
                onClick={() => setActivePhase(i)}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-medium transition-all
                  ${isActive
                    ? "bg-ow-accent border-ow-accent text-white shadow-lg shadow-ow-accent/20"
                    : "bg-ow-surface border-ow-border text-gray-400 hover:text-white hover:border-gray-500"
                  }
                `}
              >
                <span className={`w-5 h-5 flex items-center justify-center rounded-full text-xs font-bold
                  ${isActive ? "bg-white/20" : "bg-ow-border/60"}`}>
                  {i + 1}
                </span>
                <span className="truncate max-w-32">{phase.name}</span>
                {styleCfg && (
                  <span className={`w-2 h-2 rounded-full ${styleCfg.dot}`} />
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Phase active */}
      {phases.length > 0 && !guideLoading && (
        phases.length === 1
          ? <PhaseCard phase={phases[0]} index={0} total={1} />
          : <PhaseCard phase={phases[activePhase]} index={activePhase} total={phases.length} />
      )}

      {/* Map sans phases */}
      {guide && !guideLoading && phases.length === 0 && (
        <EmptyState icon="📋" message="Aucune phase définie pour cette map." />
      )}
    </div>
  );
}
