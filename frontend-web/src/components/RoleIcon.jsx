/**
 * RoleIcon — icône + couleur selon le rôle (tank / dps / support).
 */
const ROLE_CONFIG = {
  tank:    { emoji: "🛡", color: "text-blue-400",   label: "Tank" },
  dps:     { emoji: "⚔", color: "text-orange-400", label: "DPS" },
  support: { emoji: "💚", color: "text-green-400",  label: "Support" },
};

export default function RoleIcon({ role, showLabel = false, className = "" }) {
  const config = ROLE_CONFIG[role] ?? { emoji: "?", color: "text-gray-400", label: role };
  return (
    <span className={`inline-flex items-center gap-1 ${config.color} ${className}`}>
      <span>{config.emoji}</span>
      {showLabel && <span className="text-xs font-medium">{config.label}</span>}
    </span>
  );
}
