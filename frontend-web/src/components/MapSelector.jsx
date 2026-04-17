/**
 * MapSelector — menu déroulant de sélection de map.
 * Props :
 *   maps       — liste des maps de l'API
 *   value      — slug de la map sélectionnée
 *   onChange   — callback(slug)
 *   showType   — affiche le type de map dans les options
 */
const TYPE_EMOJI = {
  escort:     "🚛",
  control:    "🔵",
  hybrid:     "⚡",
  push:       "🤖",
  flashpoint: "⚡",
};

export default function MapSelector({ maps = [], value, onChange, showType = true }) {
  return (
    <select
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value || null)}
      className="bg-ow-surface border border-ow-border text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-ow-accent transition-colors cursor-pointer"
    >
      <option value="">— Sélectionner une map —</option>
      {maps.map((map) => (
        <option key={map.slug} value={map.slug}>
          {showType ? `${TYPE_EMOJI[map.map_type] ?? "🗺"} ` : ""}
          {map.name}
        </option>
      ))}
    </select>
  );
}
