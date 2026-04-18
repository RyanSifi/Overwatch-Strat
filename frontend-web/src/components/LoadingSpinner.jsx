/**
 * LoadingSpinner, ErrorMessage, EmptyState — style OW2
 */

export function LoadingSpinner({ text = "Chargement…" }) {
  return (
    <div className="flex items-center gap-3 text-gray-400 py-4">
      <div
        className="w-5 h-5 border-2 rounded-full animate-spin shrink-0"
        style={{ borderColor: "rgba(244,146,43,0.2)", borderTopColor: "#F4922B" }}
      />
      <span className="text-sm tracking-wider uppercase" style={{ fontFamily: "Rajdhani, sans-serif" }}>
        {text}
      </span>
    </div>
  );
}

export function ErrorMessage({ message = "Une erreur est survenue." }) {
  return (
    <div
      className="flex items-center gap-3 px-4 py-3 text-sm"
      style={{
        background: "rgba(255,70,85,0.08)",
        border: "1px solid rgba(255,70,85,0.3)",
        clipPath: "polygon(8px 0%, 100% 0%, calc(100% - 8px) 100%, 0% 100%)",
      }}
    >
      <span className="text-red-400 text-lg shrink-0">⚠</span>
      <span className="text-red-300" style={{ fontFamily: "Barlow, sans-serif" }}>{message}</span>
    </div>
  );
}

export function EmptyState({ icon = "🔍", message = "Aucun résultat." }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <span className="text-4xl opacity-30">{icon}</span>
      <p
        className="text-gray-500 text-sm tracking-wider uppercase"
        style={{ fontFamily: "Rajdhani, sans-serif" }}
      >
        {message}
      </p>
    </div>
  );
}
