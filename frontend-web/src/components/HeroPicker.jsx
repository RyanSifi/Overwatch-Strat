/**
 * HeroPicker — sélecteur de héros avec recherche + filtre par rôle.
 * Props :
 *   heroes     — liste complète des héros
 *   selected   — liste des slugs sélectionnés
 *   onToggle   — callback(slug) appelé au clic
 *   maxSelect  — nombre max de héros sélectionnables (défaut: 6)
 *   label      — titre du picker
 */
import { useState } from "react";
import HeroCard  from "./HeroCard";
import RoleFilter from "./RoleFilter";

export default function HeroPicker({
  heroes    = [],
  selected  = [],
  onToggle,
  maxSelect = 6,
  label     = "Sélectionne des héros",
}) {
  const [search, setSearch]     = useState("");
  const [roleFilter, setRole]   = useState(null);

  // Filtrage : recherche + rôle
  const filtered = heroes.filter((h) => {
    const matchSearch = h.name.toLowerCase().includes(search.toLowerCase());
    const matchRole   = roleFilter ? h.role === roleFilter : true;
    return matchSearch && matchRole;
  });

  const canSelect = selected.length < maxSelect;

  return (
    <div className="flex flex-col gap-3">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-white">{label}</h3>
        <span className="text-xs text-gray-500">
          {selected.length}/{maxSelect} sélectionné{selected.length > 1 ? "s" : ""}
        </span>
      </div>

      {/* Recherche */}
      <input
        type="text"
        placeholder="Rechercher un héros..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full bg-ow-surface border border-ow-border rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-ow-accent transition-colors"
      />

      {/* Filtre par rôle */}
      <RoleFilter value={roleFilter} onChange={setRole} />

      {/* Grille de héros */}
      {filtered.length === 0 ? (
        <p className="text-gray-500 text-sm text-center py-6">Aucun héros trouvé</p>
      ) : (
        <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-7 gap-2 max-h-72 overflow-y-auto pr-1">
          {filtered.map((hero) => {
            const isSelected = selected.includes(hero.slug);
            const isDisabled = !isSelected && !canSelect;
            return (
              <div
                key={hero.slug}
                className={isDisabled ? "opacity-40 pointer-events-none" : ""}
              >
                <HeroCard
                  hero={hero}
                  selected={isSelected}
                  onClick={() => onToggle(hero.slug)}
                  compact
                />
              </div>
            );
          })}
        </div>
      )}

      {/* Héros sélectionnés */}
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1 border-t border-ow-border">
          {selected.map((slug) => {
            const hero = heroes.find((h) => h.slug === slug);
            if (!hero) return null;
            return (
              <button
                key={slug}
                onClick={() => onToggle(slug)}
                className="flex items-center gap-1.5 bg-ow-accent/20 border border-ow-accent/40 text-ow-accent text-xs px-2 py-1 rounded-full hover:bg-red-500/20 hover:border-red-500/40 hover:text-red-400 transition-colors"
              >
                {hero.name}
                <span className="font-bold">×</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
