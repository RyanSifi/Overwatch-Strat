/**
 * RoleFilter — boutons de filtre par rôle (Tous / Tank / DPS / Support).
 * Props :
 *   value    — rôle actif (null = tous)
 *   onChange — callback(role)
 */
const ROLES = [
  { value: null,      label: "Tous",    emoji: "🎮" },
  { value: "tank",    label: "Tank",    emoji: "🛡" },
  { value: "dps",     label: "DPS",     emoji: "⚔" },
  { value: "support", label: "Support", emoji: "💚" },
];

export default function RoleFilter({ value, onChange }) {
  return (
    <div className="flex gap-2 flex-wrap">
      {ROLES.map(({ value: v, label, emoji }) => (
        <button
          key={v ?? "all"}
          onClick={() => onChange(v)}
          className={`
            flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border
            ${value === v
              ? "bg-ow-accent border-ow-accent text-white"
              : "bg-ow-surface border-ow-border text-gray-400 hover:text-white hover:border-gray-500"
            }
          `}
        >
          <span>{emoji}</span>
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
}
