/**
 * TeamBuilder — constructeur de comp 5v5.
 * Analyse : couverture de styles, synergies, menaces ennemies, suggestions de swap.
 */
import { useState, useEffect, useCallback } from "react";
import useHeroes     from "../hooks/useHeroes";
import { getHero }   from "../api/heroes";
import HeroPicker    from "../components/HeroPicker";
import TierBadge     from "../components/TierBadge";
import { LoadingSpinner } from "../components/LoadingSpinner";

// ─── Constantes ────────────────────────────────────────────────────────────────
const ROLE_COLOR = { tank: "#00C2FF", dps: "#F4922B", support: "#69db7c" };
const ROLE_LABEL = { tank: "Tank", dps: "DPS", support: "Support" };
const STYLE_CFG  = {
  dive:  { label: "Dive",  color: "#a855f7", bg: "rgba(168,85,247,0.1)",  border: "rgba(168,85,247,0.3)"  },
  brawl: { label: "Brawl", color: "#ef4444", bg: "rgba(239,68,68,0.1)",   border: "rgba(239,68,68,0.3)"   },
  poke:  { label: "Poke",  color: "#eab308", bg: "rgba(234,179,8,0.1)",   border: "rgba(234,179,8,0.3)"   },
};
const TIER_SCORE = { S: 5, A: 4, B: 3, C: 2, D: 1 };

// ─── Helpers ───────────────────────────────────────────────────────────────────
function avgTier(heroes) {
  if (!heroes.length) return null;
  const avg = heroes.reduce((s, h) => s + (TIER_SCORE[h.tier] ?? 3), 0) / heroes.length;
  if (avg >= 4.5) return "S"; if (avg >= 3.5) return "A";
  if (avg >= 2.5) return "B"; if (avg >= 1.5) return "C"; return "D";
}

function stylesCoverage(heroes) {
  const all = heroes.flatMap((h) => h.styles ?? []);
  return {
    dive:  all.filter((s) => s === "dive").length,
    brawl: all.filter((s) => s === "brawl").length,
    poke:  all.filter((s) => s === "poke").length,
  };
}

function roleCounts(heroes) {
  return {
    tank:    heroes.filter((h) => h.role === "tank").length,
    dps:     heroes.filter((h) => h.role === "dps").length,
    support: heroes.filter((h) => h.role === "support").length,
  };
}

// Calcule le score de ma comp vs ennemis (utilise hero.counters)
function compScore(myFull, enemySlugs) {
  return myFull.reduce((total, hero) => {
    const s = enemySlugs.reduce((t, es) => t + (hero.counters?.[es] ?? 0), 0);
    return total + s;
  }, 0);
}

// Détecte les synergies actives dans ma comp (via hero.synergies)
function activeSynergies(myFull) {
  const slugs = myFull.map((h) => h.slug);
  const found = [];
  for (const hero of myFull) {
    for (const [allySlug, score] of Object.entries(hero.synergies ?? {})) {
      if (score >= 14 && slugs.includes(allySlug) && hero.slug !== allySlug) {
        const key = [hero.slug, allySlug].sort().join(":");
        if (!found.find((f) => f.key === key)) {
          const ally = myFull.find((h) => h.slug === allySlug);
          if (ally) found.push({ key, a: hero, b: ally, score });
        }
      }
    }
  }
  return found.sort((a, b) => b.score - a.score).slice(0, 5);
}

// Détecte les menaces ennemies (enemy.counters[mySlug] > 8)
function threats(myFull, enemyFull) {
  const found = [];
  for (const enemy of enemyFull) {
    for (const myHero of myFull) {
      const sc = enemy.counters?.[myHero.slug] ?? 0;
      if (sc >= 8) found.push({ enemy, victim: myHero, score: sc });
    }
  }
  return found.sort((a, b) => b.score - a.score).slice(0, 5);
}

// Suggestions de swap : héros à remplacer + meilleure alternative contre les ennemis
function swapSuggestions(myFull, enemyFull, allHeroes) {
  if (!enemyFull.length) return [];
  const enemySlugs = enemyFull.map((h) => h.slug);
  const mySlugs    = myFull.map((h) => h.slug);

  // Trouve le héros de ma comp avec le pire score contre les ennemis
  const scored = myFull.map((hero) => ({
    hero,
    score: enemySlugs.reduce((t, es) => t + (hero.counters?.[es] ?? 0), 0),
  })).sort((a, b) => a.score - b.score);

  const suggestions = [];
  for (const { hero, score } of scored.slice(0, 2)) {
    // Cherche un remplaçant du même rôle avec un meilleur score
    const candidates = allHeroes
      .filter((h) => h.role === hero.role && !mySlugs.includes(h.slug))
      .map((h) => ({
        hero: h,
        score: enemySlugs.reduce((t, es) => t + (h.counters?.[es] ?? 0), 0),
      }))
      .filter((c) => c.score > score)
      .sort((a, b) => b.score - a.score)
      .slice(0, 1);

    if (candidates.length) {
      suggestions.push({ out: hero, in: candidates[0].hero, gain: candidates[0].score - score });
    }
  }
  return suggestions;
}

// ─── Mini carte héros ──────────────────────────────────────────────────────────
function MiniHero({ hero, onRemove, faded = false }) {
  if (!hero) return (
    <div
      className="flex items-center justify-center"
      style={{ width: 44, height: 44, background: "rgba(27,45,79,0.2)", border: "1px dashed rgba(27,45,79,0.6)", clipPath: "polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 5px 100%, 0 calc(100% - 5px))" }}
    >
      <span className="text-gray-700 text-lg">+</span>
    </div>
  );
  return (
    <div className="relative group" style={{ opacity: faded ? 0.4 : 1 }}>
      <div
        className="overflow-hidden flex items-center justify-center"
        style={{
          width: 44, height: 44,
          background: "rgba(4,7,15,0.8)",
          border: `2px solid ${ROLE_COLOR[hero.role] ?? "#444"}`,
          clipPath: "polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 5px 100%, 0 calc(100% - 5px))",
          boxShadow: `0 0 8px ${ROLE_COLOR[hero.role] ?? "#444"}40`,
        }}
      >
        {hero.icon_url
          ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover" />
          : <span className="text-xs font-bold text-white">{hero.name.slice(0,2)}</span>
        }
      </div>
      {onRemove && (
        <button
          onClick={() => onRemove(hero.slug)}
          className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold items-center justify-center hidden group-hover:flex z-10"
        >×</button>
      )}
      <p className="text-[9px] text-center text-gray-400 mt-0.5 truncate w-11" style={{ fontFamily: "Rajdhani, sans-serif" }}>{hero.name}</p>
    </div>
  );
}

// ─── Slots de comp ─────────────────────────────────────────────────────────────
function CompSlots({ heroes, allHeroes, slugs, onRemove, label, color }) {
  const slots = Array(5).fill(null).map((_, i) => allHeroes.find((h) => h.slug === slugs[i]) ?? null);
  return (
    <div className="flex flex-col gap-2">
      <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color, fontFamily: "Rajdhani, sans-serif" }}>
        {label}
      </span>
      <div className="flex gap-2 flex-wrap">
        {slots.map((hero, i) => (
          <MiniHero key={i} hero={hero} onRemove={onRemove} />
        ))}
      </div>
    </div>
  );
}

// ─── Panneau d'analyse ─────────────────────────────────────────────────────────
function AnalysisPanel({ myFull, enemyFull, allHeroesFull, loading }) {
  if (loading) return <LoadingSpinner text="Analyse en cours…" />;
  if (!myFull.length && !enemyFull.length) return (
    <div className="text-center py-10 text-gray-600 text-sm" style={{ fontFamily: "Rajdhani, sans-serif" }}>
      Sélectionne des héros pour lancer l'analyse
    </div>
  );

  const rc       = roleCounts(myFull);
  const styles   = stylesCoverage(myFull);
  const tier     = avgTier(myFull);
  const synergies = activeSynergies(myFull);
  const threatList = threats(myFull, enemyFull);
  const swaps    = swapSuggestions(myFull, enemyFull, allHeroesFull);
  const score    = compScore(myFull, enemyFull.map((h) => h.slug));

  return (
    <div className="flex flex-col gap-4">

      {/* Score global */}
      {myFull.length > 0 && enemyFull.length > 0 && (
        <div
          className="flex items-center justify-between px-4 py-3"
          style={{ background: score >= 0 ? "rgba(105,219,124,0.06)" : "rgba(255,70,85,0.06)", border: `1px solid ${score >= 0 ? "rgba(105,219,124,0.25)" : "rgba(255,70,85,0.25)"}`, clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))" }}
        >
          <span className="text-xs text-gray-400 uppercase tracking-wider" style={{ fontFamily: "Rajdhani, sans-serif" }}>Score de comp</span>
          <span className="text-2xl font-black" style={{ color: score >= 0 ? "#69db7c" : "#FF4655", fontFamily: "Rajdhani, sans-serif" }}>
            {score > 0 ? `+${score}` : score}
          </span>
        </div>
      )}

      {/* Rôles */}
      {myFull.length > 0 && (
        <Section title="Composition">
          <div className="flex gap-3">
            {["tank","dps","support"].map((r) => (
              <div key={r} className="flex flex-col items-center gap-1">
                <span className="text-lg font-black" style={{ color: rc[r] > 0 ? ROLE_COLOR[r] : "rgba(255,255,255,0.1)", fontFamily: "Rajdhani, sans-serif" }}>
                  {rc[r]}
                </span>
                <span className="text-[10px] uppercase tracking-wider" style={{ color: ROLE_COLOR[r], fontFamily: "Rajdhani, sans-serif", opacity: rc[r] > 0 ? 1 : 0.3 }}>
                  {ROLE_LABEL[r]}
                </span>
              </div>
            ))}
            {tier && (
              <div className="ml-auto flex flex-col items-center gap-1">
                <TierBadge tier={tier} size="lg" />
                <span className="text-[10px] text-gray-500 uppercase tracking-wider" style={{ fontFamily: "Rajdhani, sans-serif" }}>Moy.</span>
              </div>
            )}
          </div>
        </Section>
      )}

      {/* Styles */}
      {myFull.length > 0 && (
        <Section title="Styles couverts">
          <div className="flex gap-2 flex-wrap">
            {Object.entries(styles).map(([style, count]) => {
              const cfg = STYLE_CFG[style];
              return (
                <div
                  key={style}
                  className="flex items-center gap-2 px-3 py-1.5"
                  style={{
                    background: count > 0 ? cfg.bg   : "rgba(27,45,79,0.15)",
                    border:     `1px solid ${count > 0 ? cfg.border : "rgba(27,45,79,0.4)"}`,
                    clipPath:   "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
                    opacity:    count > 0 ? 1 : 0.4,
                  }}
                >
                  <span className="w-2 h-2 rounded-full shrink-0" style={{ background: cfg.color }} />
                  <span className="text-xs font-bold" style={{ color: cfg.color, fontFamily: "Rajdhani, sans-serif" }}>{cfg.label}</span>
                  {count > 0 && (
                    <span className="text-[10px] font-bold px-1 rounded" style={{ background: `${cfg.color}20`, color: cfg.color }}>×{count}</span>
                  )}
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {/* Synergies actives */}
      {synergies.length > 0 && (
        <Section title="⚡ Synergies actives" positive>
          <div className="flex flex-col gap-2">
            {synergies.map(({ key, a, b, score: sc }) => (
              <div key={key} className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <MiniPortrait hero={a} />
                  <span className="text-gray-600 text-xs">+</span>
                  <MiniPortrait hero={b} />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="text-xs font-bold text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                    {a.name} + {b.name}
                  </span>
                </div>
                <span className="text-[10px] font-bold px-1.5 py-0.5 shrink-0" style={{ color: "#FFD700", background: "rgba(255,215,0,0.1)", border: "1px solid rgba(255,215,0,0.2)", fontFamily: "Rajdhani, sans-serif" }}>
                  {sc >= 18 ? "Ultime" : sc >= 15 ? "Forte" : "Bonne"}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Menaces */}
      {threatList.length > 0 && (
        <Section title="⚠ Menaces détectées" negative>
          <div className="flex flex-col gap-2">
            {threatList.map(({ enemy, victim, score: sc }, i) => (
              <div key={i} className="flex items-center gap-2">
                <MiniPortrait hero={enemy} />
                <span className="text-gray-600 text-xs shrink-0">counter</span>
                <MiniPortrait hero={victim} />
                <span className="text-xs text-gray-300 flex-1 min-w-0" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                  {enemy.name} → {victim.name}
                </span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 shrink-0" style={{ color: "#FF4655", background: "rgba(255,70,85,0.1)", border: "1px solid rgba(255,70,85,0.2)", fontFamily: "Rajdhani, sans-serif" }}>
                  -{sc}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Suggestions de swap */}
      {swaps.length > 0 && (
        <Section title="💡 Suggestions de swap">
          <div className="flex flex-col gap-3">
            {swaps.map(({ out, in: swapIn, gain }, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <MiniPortrait hero={out} faded />
                  <span className="text-gray-600 text-lg">→</span>
                  <MiniPortrait hero={swapIn} />
                </div>
                <div className="flex flex-col flex-1 min-w-0">
                  <span className="text-xs font-bold text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                    Remplace {out.name} par {swapIn.name}
                  </span>
                  <span className="text-[10px] text-gray-500">Même rôle, meilleur matchup</span>
                </div>
                <span className="text-[10px] font-bold px-1.5 py-0.5 shrink-0" style={{ color: "#69db7c", background: "rgba(105,219,124,0.1)", border: "1px solid rgba(105,219,124,0.2)", fontFamily: "Rajdhani, sans-serif" }}>
                  +{gain}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {myFull.length > 0 && !synergies.length && !threatList.length && !swaps.length && (
        <div className="text-center py-4 text-gray-600 text-xs" style={{ fontFamily: "Rajdhani, sans-serif" }}>
          {enemyFull.length === 0 ? "Ajoute des ennemis pour voir les menaces et suggestions" : "Composition équilibrée, aucune faiblesse majeure détectée"}
        </div>
      )}
    </div>
  );
}

// ─── Composants utilitaires ────────────────────────────────────────────────────
function Section({ title, children, positive, negative }) {
  const color = positive ? "#69db7c" : negative ? "#FF4655" : "#F4922B";
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <div className="h-px flex-1" style={{ background: `${color}20` }} />
        <span className="text-[10px] font-bold uppercase tracking-widest shrink-0" style={{ color, fontFamily: "Rajdhani, sans-serif" }}>
          {title}
        </span>
        <div className="h-px flex-1" style={{ background: `${color}20` }} />
      </div>
      {children}
    </div>
  );
}

function MiniPortrait({ hero, faded }) {
  if (!hero) return null;
  return (
    <div
      className="overflow-hidden flex items-center justify-center shrink-0"
      style={{
        width: 22, height: 22,
        background: "rgba(4,7,15,0.8)",
        border: `1px solid ${ROLE_COLOR[hero.role] ?? "#444"}50`,
        clipPath: "polygon(0 0, calc(100% - 3px) 0, 100% 3px, 100% 100%, 3px 100%, 0 calc(100% - 3px))",
        opacity: faded ? 0.4 : 1,
      }}
    >
      {hero.icon_url
        ? <img src={hero.icon_url} alt={hero.name} style={{ width: 22, height: 22, objectFit: "cover" }} />
        : <span style={{ fontSize: 8, color: "#fff", fontWeight: "bold" }}>{hero.name.slice(0,2)}</span>
      }
    </div>
  );
}

// ─── Page principale ───────────────────────────────────────────────────────────
export default function TeamBuilder() {
  const { heroes, loading: heroesLoading } = useHeroes();
  const [mySlugs,    setMySlugs]    = useState([]);
  const [enemySlugs, setEnemySlugs] = useState([]);

  // Cache des héros complets (avec counters + synergies)
  const [fullCache, setFullCache] = useState({});
  const [fetching,  setFetching]  = useState(false);

  const allSlugs = [...new Set([...mySlugs, ...enemySlugs])];

  // Fetch les héros manquants dans le cache
  useEffect(() => {
    const missing = allSlugs.filter((s) => !fullCache[s]);
    if (!missing.length) return;
    setFetching(true);
    Promise.all(missing.map((s) => getHero(s).then((d) => [s, d])))
      .then((entries) => setFullCache((c) => ({ ...c, ...Object.fromEntries(entries) })))
      .finally(() => setFetching(false));
  }, [mySlugs, enemySlugs]);

  const myFull    = mySlugs.map((s) => fullCache[s]).filter(Boolean);
  const enemyFull = enemySlugs.map((s) => fullCache[s]).filter(Boolean);
  const allFull   = Object.values(fullCache);

  const toggleMy    = (slug) => setMySlugs((p) => p.includes(slug) ? p.filter((s) => s !== slug) : [...p, slug]);
  const toggleEnemy = (slug) => setEnemySlugs((p) => p.includes(slug) ? p.filter((s) => s !== slug) : [...p, slug]);

  if (heroesLoading) return <LoadingSpinner text="Chargement des héros…" />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-6">

      {/* Titre */}
      <div>
        <h1 className="text-3xl font-black text-white" style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.08em" }}>
          Team Builder
        </h1>
        <p className="text-gray-400 text-sm mt-1">
          Construis ta comp 5v5 et analyse les synergies, menaces et swaps recommandés.
        </p>
      </div>

      {/* Slots de comp */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          className="p-4"
          style={{ background: "rgba(0,194,255,0.04)", border: "1px solid rgba(0,194,255,0.2)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
        >
          <CompSlots label="Mon équipe" color="#00C2FF" allHeroes={heroes} slugs={mySlugs} onRemove={toggleMy} />
        </div>
        <div
          className="p-4"
          style={{ background: "rgba(255,70,85,0.04)", border: "1px solid rgba(255,70,85,0.2)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
        >
          <CompSlots label="Équipe ennemie" color="#FF4655" allHeroes={heroes} slugs={enemySlugs} onRemove={toggleEnemy} />
        </div>
      </div>

      {/* Zone principale */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px_1fr] gap-6">

        {/* Picker — Mon équipe */}
        <div
          className="p-4"
          style={{ background: "#0B1221", border: "1px solid rgba(0,194,255,0.15)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
        >
          <HeroPicker
            heroes={heroes}
            selected={mySlugs}
            onToggle={toggleMy}
            maxSelect={5}
            label="Mon équipe"
          />
        </div>

        {/* Analyse */}
        <div
          className="p-4"
          style={{ background: "#0B1221", border: "1px solid rgba(244,146,43,0.2)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
        >
          <div className="text-[10px] font-bold uppercase tracking-widest text-ow-accent mb-4" style={{ fontFamily: "Rajdhani, sans-serif" }}>
            ⚡ Analyse
          </div>
          <AnalysisPanel
            myFull={myFull}
            enemyFull={enemyFull}
            allHeroesFull={allFull}
            loading={fetching && (myFull.length < mySlugs.length || enemyFull.length < enemySlugs.length)}
          />
        </div>

        {/* Picker — Ennemis */}
        <div
          className="p-4"
          style={{ background: "#0B1221", border: "1px solid rgba(255,70,85,0.15)", clipPath: "polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px))" }}
        >
          <HeroPicker
            heroes={heroes}
            selected={enemySlugs}
            onToggle={toggleEnemy}
            maxSelect={5}
            label="Équipe ennemie"
          />
        </div>
      </div>
    </div>
  );
}
