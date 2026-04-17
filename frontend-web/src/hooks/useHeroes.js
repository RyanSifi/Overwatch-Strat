/**
 * useHeroes — charge et met en cache les héros depuis l'API.
 * Stocke dans le store Zustand pour éviter les rechargements.
 */
import { useEffect, useState } from "react";
import { getHeroes } from "../api/heroes";
import useAppStore from "../store/useAppStore";

export default function useHeroes() {
  const { heroes, setHeroes } = useAppStore();
  const [loading, setLoading] = useState(heroes.length === 0);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    if (heroes.length > 0) return; // déjà en cache
    setLoading(true);
    getHeroes()
      .then((data) => setHeroes(data.results ?? data))
      .catch((e)   => setError(e.message))
      .finally(()  => setLoading(false));
  }, []);

  return { heroes, loading, error };
}
