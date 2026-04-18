/**
 * CounterPicker — sélectionne la composition ennemie et reçoit
 * les suggestions de counters par rôle (tank / dps / support).
 */
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import useHeroes           from "../hooks/useHeroes";
import { suggestCounters } from "../api/heroes";
import HeroPicker          from "../components/HeroPicker";
import HeroCard            from "../components/HeroCard";
import TierBadge           from "../components/TierBadge";
import RoleIcon            from "../components/RoleIcon";
import SynergyPanel        from "../components/SynergyPanel";
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
  const [searchParams] = useSearchParams();

  const [enemySlugs, setEnemySlugs] = useState(() => {
    const hero = searchParams.get("hero");
    return hero ? [hero] : [];
  });
  const [result,     setResult]     = useState(null);
  const [analyzing,  setAnalyzing]  = useState(false);
  const [error,      setError]      = useState(null);
  const [activeTab,  setActiveTab]  = useState("counters"); // "counters" | "synergies"
  const [synergyHero, setSynergyHero] = useState(() => searchParams.get("hero") || null);

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
          Sélectionne la composition ennemie pour obtenir les meilleurs counters, ou explore les synergies d'un héros.
        </p>
      </div>

      {/* Onglets */}
      <div className="flex gap-1 p-1" style={{ background: "rgba(11,18,33,0.8)", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))" }}>
        {[
          { id: "counters",  label: "⚔ Counters" },
          { id: "synergies", label: "🤝 Synergies" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className="flex-1 py-2 text-sm font-bold transition-all"
            style={{
              fontFamily:  "Rajdhani, sans-serif",
              letterSpacing: "0.08em",
              background:  activeTab === tab.id ? "rgba(244,146,43,0.12)" : "transparent",
              color:       activeTab === tab.id ? "#F4922B"                : "rgba(255,255,255,0.4)",
              borderBottom: activeTab === tab.id ? "2px solid #F4922B"     : "2px solid transparent",
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Onglet Synergies ── */}
      {activeTab === "synergies" && (
        <div className="flex flex-col gap-4">
          {/* Sélecteur de héros */}
          <div
            className="p-4"
            style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
          >
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-3" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              Sélectionne un héros pour voir ses synergies
            </p>
            <div className="flex flex-wrap gap-2">
              {heroes.map((h) => (
                <button
                  key={h.slug}
                  onClick={() => setSynergyHero((v) => v === h.slug ? null : h.slug)}
                  className="flex items-center gap-1.5 px-2 py-1 text-xs transition-all"
                  style={{
                    background:   synergyHero === h.slug ? "rgba(244,146,43,0.12)" : "rgba(11,18,33,0.6)",
                    border:       `1px solid ${synergyHero === h.slug ? "#F4922B" : "rgba(27,45,79,0.8)"}`,
                    color:        synergyHero === h.slug ? "#F4922B" : "#9ca3af",
                    clipPath:     "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
                    fontFamily:   "Rajdhani, sans-serif",
                    fontWeight:   "600",
                    letterSpacing:"0.05em",
                  }}
                >
                  {h.icon_url && <img src={h.icon_url} alt="" className="w-4 h-4 object-cover rounded-sm" />}
                  {h.name}
                </button>
              ))}
            </div>
          </div>

          {/* Panneau de synergies */}
          {synergyHero ? (
            <div
              className="p-4"
              style={{ background: "#0B1221", border: "1px solid rgba(27,45,79,0.8)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
            >
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-3" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                Synergies — {heroes.find((h) => h.slug === synergyHero)?.name}
              </p>
              <SynergyPanel heroSlug={synergyHero} />
            </div>
          ) : (
            <div className="text-center py-10 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
              Sélectionne un héros ci-dessus pour voir ses synergies
            </div>
          )}
        </div>
      )}

      {/* ── Onglet Counters ── */}
      {activeTab === "counters" && (
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
      )} {/* fin onglet counters */}
    </div>
  );
}
