import { useState } from "react";
import useHeroes from "../hooks/useHeroes";
import HeroCard from "../components/HeroCard";
import TierBadge from "../components/TierBadge";
import RoleFilter from "../components/RoleFilter";
import RoleIcon from "../components/RoleIcon";
import { LoadingSpinner, ErrorMessage, EmptyState } from "../components/LoadingSpinner";

// ─── Constants ───────────────────────────────────────────────────────────────

const TIER_ORDER = ["S", "A", "B", "C", "D"];

const TIER_LABEL_STYLES = {
  S: "text-red-500 border-red-500",
  A: "text-orange-400 border-orange-400",
  B: "text-yellow-400 border-yellow-400",
  C: "text-green-400 border-green-400",
  D: "text-blue-400 border-blue-400",
};

const STYLE_FILTERS = [
  { value: null,    label: "Tous" },
  { value: "dive",  label: "Dive" },
  { value: "brawl", label: "Brawl" },
  { value: "poke",  label: "Poke" },
];

// ─── Sub-components ──────────────────────────────────────────────────────────

function StyleFilterBar({ value, onChange }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {STYLE_FILTERS.map(({ value: v, label }) => (
        <button
          key={v ?? "all"}
          onClick={() => onChange(v)}
          className={`
            px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
            ${value === v
              ? "bg-ow-accent border-ow-accent text-white"
              : "bg-ow-surface border-ow-border text-gray-400 hover:text-white hover:border-gray-500"
            }
          `}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

function TierRow({ tier, heroes, selectedId, onSelect }) {
  if (heroes.length === 0) return null;

  const labelStyle = TIER_LABEL_STYLES[tier] ?? "text-gray-400 border-gray-400";

  return (
    <div className="flex gap-4 items-start">
      {/* Tier label */}
      <div className={`
        flex-shrink-0 w-12 h-12 flex items-center justify-center
        rounded-lg border-2 text-2xl font-black
        ${labelStyle}
      `}>
        {tier}
      </div>

      {/* Hero grid */}
      <div className="flex flex-wrap gap-3 flex-1">
        {heroes.map((hero) => (
          <div key={hero.id} className="w-20">
            <HeroCard
              hero={hero}
              compact
              selected={selectedId === hero.id}
              onClick={() => onSelect(hero)}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function HeroDetailPanel({ hero, onClose }) {
  if (!hero) return null;

  return (
    <div className="card bg-ow-surface border border-ow-border rounded-xl p-5 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          {/* Avatar */}
          <div className="w-14 h-14 rounded-xl bg-ow-border/40 flex items-center justify-center font-bold text-white text-lg flex-shrink-0">
            {hero.icon_url
              ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover rounded-xl" />
              : hero.name.slice(0, 2).toUpperCase()
            }
          </div>
          <div>
            <h2 className="text-lg font-bold text-white leading-tight">{hero.name}</h2>
            <div className="flex items-center gap-2 mt-0.5">
              <RoleIcon role={hero.role} showLabel />
              {hero.is_new && (
                <span className="bg-ow-accent text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
                  NEW
                </span>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={onClose}
          className="text-gray-500 hover:text-white transition-colors text-xl leading-none flex-shrink-0"
          aria-label="Fermer"
        >
          ×
        </button>
      </div>

      {/* Stats row */}
      <div className="flex flex-wrap gap-3 text-sm">
        <div className="flex flex-col gap-1">
          <span className="text-gray-500 text-xs uppercase tracking-wider">Tier</span>
          <TierBadge tier={hero.tier} size="lg" />
        </div>

        {hero.subrole && (
          <div className="flex flex-col gap-1">
            <span className="text-gray-500 text-xs uppercase tracking-wider">Sous-rôle</span>
            <span className="badge text-gray-300 capitalize">{hero.subrole}</span>
          </div>
        )}
      </div>

      {/* Play styles */}
      {hero.styles && hero.styles.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <span className="text-gray-500 text-xs uppercase tracking-wider">Styles de jeu</span>
          <div className="flex flex-wrap gap-2">
            {hero.styles.map((style) => (
              <span
                key={style}
                className="badge bg-ow-border/60 text-gray-300 capitalize px-2.5 py-1 rounded-lg text-xs font-medium border border-ow-border"
              >
                {style}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function TierList() {
  const { heroes, loading, error } = useHeroes();
  const [roleFilter, setRoleFilter]   = useState(null);
  const [styleFilter, setStyleFilter] = useState(null);
  const [selectedHero, setSelectedHero] = useState(null);

  // ── Filtering ──────────────────────────────────────────────────────────────
  const filtered = heroes.filter((hero) => {
    if (roleFilter  && hero.role !== roleFilter)                       return false;
    if (styleFilter && !hero.styles?.includes(styleFilter))           return false;
    return true;
  });

  // ── Group by tier ──────────────────────────────────────────────────────────
  const byTier = TIER_ORDER.reduce((acc, tier) => {
    acc[tier] = filtered.filter((h) => h.tier === tier);
    return acc;
  }, {});

  const hasResults = filtered.length > 0;

  // ── Handlers ───────────────────────────────────────────────────────────────
  function handleSelectHero(hero) {
    setSelectedHero((prev) => (prev?.id === hero.id ? null : hero));
  }

  function handleCloseDetail() {
    setSelectedHero(null);
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">

      {/* Page title */}
      <div>
        <h1 className="text-3xl font-black text-white">Tier List</h1>
        <p className="text-gray-400 mt-1 text-sm">
          Classement des héros par efficacité dans le méta actuel.
        </p>
      </div>

      {/* Filters */}
      <div className="card bg-ow-surface border border-ow-border rounded-xl p-4 space-y-3">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
          <div className="flex flex-col gap-1.5">
            <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">Rôle</span>
            <RoleFilter value={roleFilter} onChange={setRoleFilter} />
          </div>
        </div>
        <div className="flex flex-col gap-1.5">
          <span className="text-xs text-gray-500 uppercase tracking-wider font-medium">Style</span>
          <StyleFilterBar value={styleFilter} onChange={setStyleFilter} />
        </div>
      </div>

      {/* Loading / Error */}
      {loading && <LoadingSpinner text="Chargement des héros..." />}
      {error   && <ErrorMessage message={error} />}

      {/* Detail panel (shown when a hero is selected) */}
      {selectedHero && (
        <HeroDetailPanel hero={selectedHero} onClose={handleCloseDetail} />
      )}

      {/* Tier rows */}
      {!loading && !error && (
        hasResults
          ? (
            <div className="space-y-3">
              {TIER_ORDER.map((tier) => (
                <div
                  key={tier}
                  className={`
                    card bg-ow-surface border border-ow-border rounded-xl p-4 transition-all
                    ${byTier[tier].length === 0 ? "hidden" : ""}
                  `}
                >
                  <TierRow
                    tier={tier}
                    heroes={byTier[tier]}
                    selectedId={selectedHero?.id}
                    onSelect={handleSelectHero}
                  />
                </div>
              ))}
            </div>
          )
          : (
            <EmptyState
              message="Aucun héros ne correspond aux filtres sélectionnés."
              icon="🔍"
            />
          )
      )}
    </div>
  );
}
