/**
 * FavoriteButton — étoile toggle pour marquer un héros ou une map en favori.
 * Usage :
 *   <FavoriteButton type="hero" slug="ana" />
 *   <FavoriteButton type="map"  slug="kings-row" size="sm" />
 */
import useAppStore from "../store/useAppStore";

export default function FavoriteButton({ type = "hero", slug, size = "md", className = "" }) {
  const favoriteHeroes    = useAppStore((s) => s.favoriteHeroes);
  const favoriteMaps      = useAppStore((s) => s.favoriteMaps);
  const toggleFavoriteHero = useAppStore((s) => s.toggleFavoriteHero);
  const toggleFavoriteMap  = useAppStore((s) => s.toggleFavoriteMap);

  const isFav = type === "hero"
    ? favoriteHeroes.includes(slug)
    : favoriteMaps.includes(slug);

  const toggle = (e) => {
    e.stopPropagation();
    if (type === "hero") toggleFavoriteHero(slug);
    else                 toggleFavoriteMap(slug);
  };

  const sizeClass = size === "sm" ? "w-4 h-4 text-[13px]" : "w-5 h-5 text-[16px]";

  return (
    <button
      onClick={toggle}
      title={isFav ? "Retirer des favoris" : "Ajouter aux favoris"}
      className={`flex items-center justify-center transition-all hover:scale-110 active:scale-95 ${sizeClass} ${className}`}
      style={{
        color:      isFav ? "#FFD700" : "rgba(255,255,255,0.2)",
        filter:     isFav ? "drop-shadow(0 0 4px rgba(255,215,0,0.6))" : "none",
        background: "transparent",
        border:     "none",
        padding:    0,
        cursor:     "pointer",
      }}
    >
      {isFav ? "★" : "☆"}
    </button>
  );
}
