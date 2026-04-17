/**
 * Guide — stratégies par map et par phase.
 *
 * 1. MapSelector en haut pour choisir une map.
 * 2. Fetch du guide pour le slug sélectionné via getMapGuide().
 * 3. Chaque phase affichée sous forme de card :
 *    - Nom de la phase + badge style (dive / brawl / poke) + notes
 *    - 3 colonnes Tank | DPS | Support avec HeroCard compact
 */
import { useState, useEffect } from "react";
import useMaps                 from "../hooks/useMaps";
import { getMapGuide }         from "../api/maps";
import MapSelector             from "../components/MapSelector";
import HeroCard                from "../components/HeroCard";
import RoleIcon                from "../components/RoleIcon";
import { LoadingSpinner, ErrorMessage, EmptyState } from "../components/LoadingSpinner";

// ─── Style badge pour le style de jeu ──────────────────────────────────────────
const STYLE_CONFIG = {
  dive:  { label: "Dive",  classes: "bg-purple-500/20 text-purple-300 border-purple-500/40" },
  brawl: { label: "Brawl", classes: "bg-red-500/20    text-red-300    border-red-500/40"    },
  poke:  { label: "Poke",  classes: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40" },
};

function StyleBadge({ style }) {
  const cfg = STYLE_CONFIG[style?.toLowerCase()] ?? {
    label: style ?? "—",
    classes: "bg-gray-500/20 text-gray-400 border-gray-500/40",
  };
  return (
    <span className={`inline-flex items-center border rounded px-2 py-0.5 text-xs font-bold uppercase tracking-wide ${cfg.classes}`}>
      {cfg.label}
    </span>
  );
}

// ─── Colonne de héros par rôle ─────────────────────────────────────────────────
const ROLE_HEADER = {
  tank:    { label: "Tank",    accent: "text-blue-400",   border: "border-blue-400/30"   },
  dps:     { label: "DPS",     accent: "text-orange-400", border: "border-orange-400/30" },
  support: { label: "Support", accent: "text-green-400",  border: "border-green-400/30"  },
};

function RoleColumn({ role, heroes = [] }) {
  const cfg = ROLE_HEADER[role] ?? { label: role, accent: "text-gray-400", border: "border-gray-400/30" };

  return (
    <div className="flex flex-col gap-3">
      {/* En-tête de colonne */}
      <div className={`flex items-center gap-2 pb-2 border-b ${cfg.border}`}>
        <RoleIcon role={role} showLabel />
        <span className={`text-xs font-bold uppercase tracking-wider ${cfg.accent}`}>
          {cfg.label}
        </span>
        <span className="ml-auto text-xs text-gray-600">{heroes.length}</span>
      </div>

      {/* Hero cards */}
      {heroes.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {heroes.map((hero) => (
            <HeroCard key={hero.slug} hero={hero} compact />
          ))}
        </div>
      ) : (
        <p className="text-xs text-gray-600 italic">Aucun héros recommandé.</p>
      )}
    </div>
  );
}

// ─── Card d'une phase ──────────────────────────────────────────────────────────
function PhaseCard({ phase, index }) {
  const { tank = [], dps = [], support = [] } = phase.recommended ?? {};

  return (
    <div className="card flex flex-col gap-5">
      {/* Titre de la phase */}
      <div className="flex flex-wrap items-center gap-3 pb-3 border-b border-ow-border">
        <span className="w-7 h-7 flex items-center justify-center rounded-full bg-ow-accent/20 text-ow-accent text-sm font-bold shrink-0">
          {index + 1}
        </span>
        <h2 className="font-bold text-white text-base">{phase.name}</h2>
        {phase.style && <StyleBadge style={phase.style} />}
      </div>

      {/* Notes stratégiques */}
      {phase.notes && (
        <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">
          {phase.notes}
        </p>
      )}

      {/* Grille Tank | DPS | Support */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
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

  const [selectedSlug, setSelectedSlug] = useState(null);
  const [guide,        setGuide]        = useState(null);
  const [guideLoading, setGuideLoading] = useState(false);
  const [guideError,   setGuideError]   = useState(null);

  // Fetch du guide quand le slug change
  useEffect(() => {
    if (!selectedSlug) {
      setGuide(null);
      setGuideError(null);
      return;
    }

    setGuideLoading(true);
    setGuideError(null);
    setGuide(null);

    getMapGuide(selectedSlug)
      .then((data) => setGuide(data))
      .catch((e)   => setGuideError(e.response?.data?.detail ?? e.message))
      .finally(()  => setGuideLoading(false));
  }, [selectedSlug]);

  // ─── Rendu ──────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      {/* Titre */}
      <div>
        <h1 className="text-2xl font-bold text-white">Guide des maps</h1>
        <p className="text-gray-400 text-sm mt-1">
          Stratégies et compositions recommandées, phase par phase.
        </p>
      </div>

      {/* Sélecteur de map */}
      <div className="card flex flex-wrap items-center gap-4">
        <span className="text-sm text-gray-400 font-medium shrink-0">Choisir une map :</span>

        {mapsLoading && <LoadingSpinner text="Chargement des maps…" />}
        {mapsError   && <ErrorMessage message={mapsError} />}

        {!mapsLoading && !mapsError && (
          <MapSelector
            maps={maps}
            value={selectedSlug}
            onChange={setSelectedSlug}
            showType
          />
        )}

        {/* Nom de la map sélectionnée */}
        {selectedSlug && guide && (
          <span className="ml-auto text-xs text-gray-500 capitalize">
            {guide.map?.map_type && (
              <span className="badge mr-2 capitalize">{guide.map.map_type}</span>
            )}
            {guide.map?.name}
          </span>
        )}
      </div>

      {/* États : aucune map sélectionnée */}
      {!selectedSlug && (
        <EmptyState
          icon="🗺"
          message="Sélectionne une map pour afficher son guide stratégique."
        />
      )}

      {/* Chargement du guide */}
      {selectedSlug && guideLoading && (
        <LoadingSpinner text="Chargement du guide…" />
      )}

      {/* Erreur guide */}
      {selectedSlug && guideError && (
        <ErrorMessage message={guideError} />
      )}

      {/* Phases */}
      {guide && !guideLoading && (
        <>
          {guide.phases && guide.phases.length > 0 ? (
            <div className="flex flex-col gap-5">
              {guide.phases.map((phase, i) => (
                <PhaseCard key={phase.name ?? i} phase={phase} index={i} />
              ))}
            </div>
          ) : (
            <EmptyState
              icon="📋"
              message="Aucune phase définie pour cette map."
            />
          )}
        </>
      )}
    </div>
  );
}
