/**
 * HeroCard — carte d'un héros avec son nom, tier, rôle et badge "NEW".
 * Props :
 *   hero       — objet héros de l'API
 *   selected   — boolean (bordure bleue si sélectionné)
 *   onClick    — callback de clic
 *   showScore  — affiche un score de counter si fourni
 *   score      — valeur numérique du score
 *   compact    — mode compact (grille dense)
 */
import TierBadge from "./TierBadge";
import RoleIcon  from "./RoleIcon";

const ROLE_BORDER = {
  tank:    "hover:border-blue-400/60",
  dps:     "hover:border-orange-400/60",
  support: "hover:border-green-400/60",
};

export default function HeroCard({
  hero,
  selected  = false,
  onClick   = null,
  showScore = false,
  score     = null,
  compact   = false,
}) {
  const borderHover = ROLE_BORDER[hero.role] ?? "hover:border-gray-400/60";

  return (
    <div
      onClick={onClick}
      className={`
        relative bg-ow-surface border rounded-xl transition-all
        ${onClick ? "cursor-pointer" : ""}
        ${selected
          ? "border-ow-accent shadow-lg shadow-ow-accent/20 scale-105"
          : `border-ow-border ${borderHover}`
        }
        ${compact ? "p-2" : "p-3"}
      `}
    >
      {/* Badge NEW */}
      {hero.is_new && (
        <span className="absolute -top-1.5 -right-1.5 bg-ow-accent text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full">
          NEW
        </span>
      )}

      {/* Icône placeholder (initiale si pas d'icon_url) */}
      <div className={`
        flex items-center justify-center rounded-lg bg-ow-border/40 font-bold text-white
        ${compact ? "w-12 h-12 text-base mx-auto" : "w-14 h-14 text-xl mx-auto"}
      `}>
        {hero.icon_url
          ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover rounded-lg" />
          : hero.name.slice(0, 2).toUpperCase()
        }
      </div>

      {/* Nom */}
      <p className={`text-center font-semibold mt-2 leading-tight truncate
        ${compact ? "text-xs" : "text-sm"}
      `}>
        {hero.name}
      </p>

      {/* Tier + rôle */}
      {!compact && (
        <div className="flex items-center justify-center gap-1.5 mt-1.5">
          <TierBadge tier={hero.tier} />
          <RoleIcon role={hero.role} />
        </div>
      )}

      {/* Score counter (si affiché) */}
      {showScore && score !== null && (
        <div className={`mt-1.5 text-center text-xs font-bold ${
          score > 0 ? "text-green-400" : "text-red-400"
        }`}>
          {score > 0 ? `+${score}` : score}
        </div>
      )}
    </div>
  );
}
