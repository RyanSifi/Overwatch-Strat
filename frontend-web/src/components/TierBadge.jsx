/**
 * TierBadge — affiche le tier d'un héros (S/A/B/C/D) avec la couleur associée.
 */
const TIER_STYLES = {
  S: "bg-red-500/20 text-red-400 border-red-500/40",
  A: "bg-orange-500/20 text-orange-400 border-orange-500/40",
  B: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
  C: "bg-green-500/20 text-green-400 border-green-500/40",
  D: "bg-blue-500/20 text-blue-400 border-blue-500/40",
};

export default function TierBadge({ tier, size = "sm" }) {
  const style = TIER_STYLES[tier] ?? "bg-gray-500/20 text-gray-400 border-gray-500/40";
  const sizeClass = size === "lg" ? "text-sm px-2.5 py-1 text-base font-bold" : "text-xs px-1.5 py-0.5 font-bold";

  return (
    <span className={`inline-flex items-center rounded border ${style} ${sizeClass}`}>
      {tier}
    </span>
  );
}
