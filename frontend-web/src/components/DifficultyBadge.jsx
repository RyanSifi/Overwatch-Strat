/**
 * DifficultyBadge — affiche la difficulté d'un héros (1/2/3) style OW2.
 * Peut s'afficher en mode "badge" compact ou en mode "detail" avec description.
 */

const DIFFICULTY = {
  1: {
    label:  "Facile",
    desc:   "Prise en main rapide, kit simple, idéal pour débuter",
    color:  "#69db7c",
    glow:   "rgba(105,219,124,0.3)",
    filled: 1,
  },
  2: {
    label:  "Moyen",
    desc:   "Requiert de la pratique pour maîtriser ses capacités",
    color:  "#F4922B",
    glow:   "rgba(244,146,43,0.3)",
    filled: 2,
  },
  3: {
    label:  "Difficile",
    desc:   "Haut skill ceiling, récompense fortement la maîtrise",
    color:  "#FF4655",
    glow:   "rgba(255,70,85,0.3)",
    filled: 3,
  },
};

// 3 barres de difficulté
function DifficultyBars({ level, color, glow }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="h-2 transition-all"
          style={{
            width: "18px",
            background: i <= level ? color : "rgba(255,255,255,0.08)",
            boxShadow: i <= level ? `0 0 6px ${glow}` : "none",
            clipPath: "polygon(3px 0%, 100% 0%, calc(100% - 3px) 100%, 0% 100%)",
          }}
        />
      ))}
    </div>
  );
}

export default function DifficultyBadge({ difficulty = 2, detail = false }) {
  const cfg = DIFFICULTY[difficulty] ?? DIFFICULTY[2];

  if (detail) {
    return (
      <div className="flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <span
            className="text-xs font-bold uppercase tracking-widest"
            style={{ color: cfg.color, fontFamily: "Rajdhani, sans-serif" }}
          >
            {cfg.label}
          </span>
          <DifficultyBars level={cfg.filled} color={cfg.color} glow={cfg.glow} />
        </div>
        <p className="text-xs text-gray-500 leading-relaxed" style={{ fontFamily: "Barlow, sans-serif" }}>
          {cfg.desc}
        </p>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <DifficultyBars level={cfg.filled} color={cfg.color} glow={cfg.glow} />
      <span
        className="text-[10px] font-bold uppercase tracking-wider"
        style={{ color: cfg.color, fontFamily: "Rajdhani, sans-serif" }}
      >
        {cfg.label}
      </span>
    </div>
  );
}
