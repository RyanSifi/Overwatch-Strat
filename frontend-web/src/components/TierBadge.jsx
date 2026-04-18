/**
 * TierBadge — affiche le tier d'un héros (S/A/B/C/D) style OW2.
 */
const TIER_STYLES = {
  S: { bg: "rgba(255,70,85,0.15)",  border: "rgba(255,70,85,0.6)",  text: "#FF4655", glow: "rgba(255,70,85,0.3)"  },
  A: { bg: "rgba(244,146,43,0.15)", border: "rgba(244,146,43,0.6)", text: "#F4922B", glow: "rgba(244,146,43,0.3)" },
  B: { bg: "rgba(255,215,0,0.12)",  border: "rgba(255,215,0,0.5)",  text: "#FFD700", glow: "rgba(255,215,0,0.2)"  },
  C: { bg: "rgba(105,219,124,0.12)",border: "rgba(105,219,124,0.5)",text: "#69db7c", glow: "rgba(105,219,124,0.2)"},
  D: { bg: "rgba(0,194,255,0.12)",  border: "rgba(0,194,255,0.5)",  text: "#00C2FF", glow: "rgba(0,194,255,0.2)"  },
};

export default function TierBadge({ tier, size = "sm" }) {
  const s = TIER_STYLES[tier] ?? { bg: "rgba(100,100,100,0.15)", border: "rgba(100,100,100,0.4)", text: "#aaa", glow: "none" };
  const pad   = size === "lg" ? "px-3 py-1 text-base" : "px-1.5 py-0.5 text-xs";
  const style = {
    background:  s.bg,
    border:      `1px solid ${s.border}`,
    color:       s.text,
    boxShadow:   `0 0 8px ${s.glow}`,
    fontFamily:  "Rajdhani, sans-serif",
    fontWeight:  700,
    letterSpacing: "0.1em",
    clipPath:    "polygon(4px 0%, 100% 0%, calc(100% - 4px) 100%, 0% 100%)",
  };

  return (
    <span className={`inline-flex items-center ${pad}`} style={style}>
      {tier}
    </span>
  );
}
