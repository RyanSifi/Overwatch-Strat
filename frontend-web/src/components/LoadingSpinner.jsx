/**
 * LoadingSpinner + états génériques : loading, error, empty.
 */
export function LoadingSpinner({ text = "Chargement..." }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-12 text-gray-500">
      <div className="w-8 h-8 border-2 border-ow-border border-t-ow-accent rounded-full animate-spin" />
      <span className="text-sm">{text}</span>
    </div>
  );
}

export function ErrorMessage({ message = "Une erreur est survenue." }) {
  return (
    <div className="card border-red-500/30 bg-red-500/10 text-red-400 text-sm flex items-center gap-2 py-3">
      <span>⚠</span>
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({ message = "Aucun résultat.", icon = "🔍" }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-gray-500">
      <span className="text-4xl">{icon}</span>
      <p className="text-sm">{message}</p>
    </div>
  );
}
