import { useEffect, useState } from "react";
import { getMaps } from "../api/maps";

export default function useMaps() {
  const [maps,    setMaps]    = useState([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    getMaps()
      .then((data) => setMaps(data.results ?? data))
      .catch((e)   => setError(e.message))
      .finally(()  => setLoading(false));
  }, []);

  return { maps, loading, error };
}
