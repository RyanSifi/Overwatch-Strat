/**
 * MapSelector — menu déroulant de sélection de map.
 * Les maps favorites apparaissent en premier avec une étoile.
 * Props :
 *   maps       — liste des maps de l'API
 *   value      — slug de la map sélectionnée
 *   onChange   — callback(slug)
 *   showType   — affiche le type de map dans les options
 */
import useAppStore from "../store/useAppStore";

const TYPE_EMOJI = {
  escort:     "🚛",
  control:    "🔵",
  hybrid:     "⚡",
  push:       "🤖",
  flashpoint: "💥",
};

export default function MapSelector({ maps = [], value, onChange, showType = true }) {
  const favoriteMaps = useAppStore((s) => s.favoriteMaps);

  const favorites    = maps.filter((m) => favoriteMaps.includes(m.slug));
  const others       = maps.filter((m) => !favoriteMaps.includes(m.slug));

  const renderOption = (map, fav = false) => (
    <option key={map.slug} value={map.slug}>
      {fav ? "★ " : ""}
      {showType ? `${TYPE_EMOJI[map.map_type] ?? "🗺"} ` : ""}
      {map.name}
    </option>
  );

  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="bg-ow-surface border border-ow-border text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ow-accent transition-colors cursor-pointer"
    >
      <option value="">— Sélectionner une map —</option>

      {favorites.length > 0 && (
        <optgroup label="⭐ Favoris">
          {favorites.map((m) => renderOption(m, true))}
        </optgroup>
      )}

      {favorites.length > 0
        ? <optgroup label="Toutes les maps">{others.map((m) => renderOption(m))}</optgroup>
        : others.map((m) => renderOption(m))
      }
    </select>
  );
}
