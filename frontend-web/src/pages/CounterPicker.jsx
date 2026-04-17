/**
 * CounterPicker — sélectionne la composition ennemie et reçoit
 * les suggestions de counters par rôle (tank / dps / support).
 */
import { useState } from "react";
import useHeroes           from "../hooks/useHeroes";
import { suggestCounters } from "../api/heroes";
import HeroPicker          from "../components/HeroPicker";
import HeroCard            from "../components/HeroCard";
import TierBadge           from "../components/TierBadge";
import RoleIcon            from "../components/RoleIcon";
import { LoadingSpinner, ErrorMessage, EmptyState } from "../components/LoadingSpinner";

// ─── Carte d'une suggestion ────────────────────────────────────────────────────
function SuggestionCard({ hero }) {
  return (
    <div className="card flex gap-3 items-start hover:border-ow-accent/40 transition-colors">
      {/* Avatar */}
      <div className="shrink-0">
        <HeroCard hero={hero} compact />
      </div>

      {/* Infos */}
      <div className="flex flex-col gap-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-white text-sm">{hero.name}</span>
          <TierBadge tier={hero.tier} />
          {hero.subrole && (
            <span className="text-xs text-gray-500 capitalize">{hero.subrole}</span>
          )}
        </div>

        <div className="flex flex-col gap-1">
          {hero.reason.split("\n").map((line, i) => (
            <p key={i} className="text-xs text-gray-400 leading-relaxed">{line}</p>
          ))}
        </div>

        {/* Score bar */}
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 h-1.5 bg-ow-border rounded-full overflow-hidden">
            <div
              className="h-full bg-ow-accent rounded-full transition-all"
              style={{ width: `${Math.min(100, hero.total_score * 8)}%` }}
            />
          </div>
          <span className="text-xs text-ow-accent font-mono">+{hero.total_score}</span>
        </div>
      </div>
    </div>
  );
}

// ─── Bloc par rôle ─────────────────────────────────────────────────────────────
const ROLE_LABELS = { tank: "Tank", dps: "DPS", support: "Support" };

function RoleSection({ role, heroes }) {
  if (!heroes || heroes.length === 0) return null;
  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-2 pb-1 border-b border-ow-border">
        <RoleIcon role={role} showLabel />
        <h3 className="font-semibold text-white text-sm uppercase tracking-wide">
          {ROLE_LABELS[role]}
        </h3>
        <span className="text-xs text-gray-500 ml-auto">{heroes.length} suggestion{heroes.length > 1 ? "s" : ""}</span>
      </div>
      <div className="flex flex-col gap-2">
        {heroes.map((h) => (
          <SuggestionCard key={h.slug} hero={h} />
        ))}
      </div>
    </div>
  );
}

// ─── Page principale ───────────────────────────────────────────────────────────
export default function CounterPicker() {
  const { heroes, loading: heroesLoading, error: heroesError } = useHeroes();

  const [enemySlugs, setEnemySlugs] = useState([]);
  const [result,     setResult]     = useState(null);
  const [analyzing,  setAnalyzing]  = useState(false);
  const [error,      setError]      = useState(null);

  const toggleEnemy = (slug) => {
    setEnemySlugs((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
    // Reset résultat si la sélection change
    setResult(null);
    setError(null);
  };

  const handleAnalyze = async () => {
    if (enemySlugs.length === 0) return;
    setAnalyzing(true);
    setError(null);
    setResult(null);
    try {
      const data = await suggestCounters(enemySlugs);
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.error ?? e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const hasResults =
    result &&
    (result.suggestions.tank.length > 0 ||
      result.suggestions.dps.length > 0 ||
      result.suggestions.support.length > 0);

  // ─── Rendu ────────────────────────────────────────────────────────────────────
  if (heroesLoading) return <LoadingSpinner text="Chargement des héros..." />;
  if (heroesError)   return <ErrorMessage message={heroesError} />;

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      {/* Titre */}
      <div>
        <h1 className="text-2xl font-bold text-white">Counter Picker</h1>
        <p className="text-gray-400 text-sm mt-1">
          Sélectionne la composition ennemie (jusqu'à 6 héros) pour obtenir les meilleurs counters.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ── Panneau gauche : sélection ennemie ── */}
        <div className="card flex flex-col gap-4">
          <HeroPicker
            heroes={heroes}
            selected={enemySlugs}
            onToggle={toggleEnemy}
            maxSelect={6}
            label="Composition ennemie"
          />

          <button
            onClick={handleAnalyze}
            disabled={enemySlugs.length === 0 || analyzing}
            className="btn-primary disabled:opacity-40 disabled:cursor-not-allowed mt-2"
          >
            {analyzing ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Analyse en cours…
              </span>
            ) : (
              `Analyser ${enemySlugs.length > 0 ? `(${enemySlugs.length} ennemi${enemySlugs.length > 1 ? "s" : ""})` : ""}`
            )}
          </button>
        </div>

        {/* ── Panneau droit : suggestions ── */}
        <div className="flex flex-col gap-4">
          {error && <ErrorMessage message={error} />}

          {!result && !analyzing && !error && (
            <EmptyState
              icon="🎯"
              message="Sélectionne des héros ennemis puis clique sur Analyser."
            />
          )}

          {analyzing && <LoadingSpinner text="Calcul des counters…" />}

          {result && !hasResults && (
            <EmptyState
              icon="😅"
              message="Aucun counter trouvé pour cette composition. Essaie d'autres héros."
            />
          )}

          {hasResults && (
            <div className="flex flex-col gap-5">
              {/* Ennemis analysés */}
              <div className="flex flex-wrap gap-2">
                {result.enemy_heroes.map((slug) => {
                  const h = heroes.find((x) => x.slug === slug);
                  return (
                    <span
                      key={slug}
                      className="flex items-center gap-1.5 bg-red-500/10 border border-red-500/30 text-red-400 text-xs px-2 py-1 rounded-full"
                    >
                      <RoleIcon role={h?.role} className="text-xs" />
                      {h?.name ?? slug}
                    </span>
                  );
                })}
              </div>

              <RoleSection role="tank"    heroes={result.suggestions.tank} />
              <RoleSection role="dps"     heroes={result.suggestions.dps} />
              <RoleSection role="support" heroes={result.suggestions.support} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
