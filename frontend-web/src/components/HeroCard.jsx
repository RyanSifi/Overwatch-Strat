/**
 * HeroCard — carte héros style OW2.
 * Design angulaire, bordure colorée par rôle, glow au survol.
 */
import TierBadge from "./TierBadge";
import FavoriteButton from "./FavoriteButton";

const ROLE_STYLE = {
  tank:    { border: "#00C2FF", glow: "rgba(0,194,255,0.3)",    bg: "rgba(0,194,255,0.05)"    },
  dps:     { border: "#F4922B", glow: "rgba(244,146,43,0.3)",   bg: "rgba(244,146,43,0.05)"   },
  support: { border: "#69db7c", glow: "rgba(105,219,124,0.3)",  bg: "rgba(105,219,124,0.05)"  },
};

export default function HeroCard({
  hero,
  selected      = false,
  onClick       = null,
  showScore     = false,
  score         = null,
  compact       = false,
  showFavorite  = true,
}) {
  const rs = ROLE_STYLE[hero.role] ?? { border: "#444", glow: "rgba(100,100,100,0.2)", bg: "rgba(100,100,100,0.05)" };

  const baseStyle = {
    background: selected ? `${rs.bg}` : "rgba(11,18,33,0.8)",
    border: `1px solid ${selected ? rs.border : "rgba(27,45,79,0.8)"}`,
    boxShadow: selected ? `0 0 16px ${rs.glow}, inset 0 0 20px ${rs.bg}` : "none",
    clipPath: "polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))",
    transition: "all 0.2s ease",
    cursor: onClick ? "pointer" : "default",
  };

  const hoverStyle = `group`;

  return (
    <div
      onClick={onClick}
      className={`relative ${hoverStyle}`}
      style={baseStyle}
      onMouseEnter={e => {
        if (!selected) {
          e.currentTarget.style.border = `1px solid ${rs.border}`;
          e.currentTarget.style.boxShadow = `0 0 12px ${rs.glow}`;
        }
      }}
      onMouseLeave={e => {
        if (!selected) {
          e.currentTarget.style.border = "1px solid rgba(27,45,79,0.8)";
          e.currentTarget.style.boxShadow = "none";
        }
      }}
    >
      {/* Badge NEW */}
      {hero.is_new && (
        <span
          className="absolute -top-1 -right-1 text-white text-[8px] font-bold px-1.5 py-0.5 z-10"
          style={{
            background: "linear-gradient(90deg, #F4922B, #e07820)",
            clipPath: "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
            fontFamily: "Rajdhani, sans-serif",
            letterSpacing: "0.1em",
          }}
        >
          NEW
        </span>
      )}

      {/* Bouton favori — visible au survol */}
      {showFavorite && (
        <div className="absolute top-0.5 left-0.5 z-10 opacity-0 group-hover:opacity-100 transition-opacity">
          <FavoriteButton type="hero" slug={hero.slug} size="sm" />
        </div>
      )}

      <div className={compact ? "p-2" : "p-3"}>
        {/* Portrait */}
        <div
          className={`flex items-center justify-center overflow-hidden mx-auto ${compact ? "w-11 h-11" : "w-14 h-14"}`}
          style={{
            background: "rgba(4,7,15,0.6)",
            border: `1px solid ${rs.border}30`,
            clipPath: "polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 5px 100%, 0 calc(100% - 5px))",
          }}
        >
          {hero.icon_url
            ? <img src={hero.icon_url} alt={hero.name} className="w-full h-full object-cover" />
            : <span className="text-sm font-bold text-white" style={{ fontFamily: "Rajdhani, sans-serif" }}>
                {hero.name.slice(0, 2).toUpperCase()}
              </span>
          }
        </div>

        {/* Nom */}
        <p
          className={`text-center font-bold mt-1.5 leading-tight truncate ${compact ? "text-[11px]" : "text-xs"}`}
          style={{ fontFamily: "Rajdhani, sans-serif", letterSpacing: "0.05em", color: selected ? "#fff" : "#cbd5e1" }}
        >
          {hero.name}
        </p>

        {/* Tier + rôle (mode normal seulement) */}
        {!compact && (
          <div className="flex items-center justify-center mt-1.5">
            <TierBadge tier={hero.tier} />
          </div>
        )}

        {/* Score counter */}
        {showScore && score !== null && (
          <div
            className="mt-1 text-center text-xs font-bold"
            style={{
              fontFamily: "Rajdhani, sans-serif",
              color: score > 0 ? "#69db7c" : "#FF4655",
            }}
          >
            {score > 0 ? `+${score}` : score}
          </div>
        )}
      </div>
    </div>
  );
}
