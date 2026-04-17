import { useState, useEffect } from "react";
import { getSessions, createSession, deleteSession, getStats } from "../api/tracker";
import useAppStore from "../store/useAppStore";

export function useSessions() {
  const { user } = useAppStore();
  const [sessions, setSessions] = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const load = () => {
    if (!user) return;
    setLoading(true);
    getSessions()
      .then((d) => setSessions(d.results ?? d))
      .catch((e) => setError(e.message))
      .finally(()  => setLoading(false));
  };

  useEffect(load, [user]);

  const add = async (data) => {
    const session = await createSession(data);
    setSessions((prev) => [session, ...prev]);
    return session;
  };

  const remove = async (id) => {
    await deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
  };

  return { sessions, loading, error, add, remove, reload: load };
}

export function useStats() {
  const { user } = useAppStore();
  const [stats,   setStats]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    getStats()
      .then(setStats)
      .catch((e) => setError(e.message))
      .finally(()  => setLoading(false));
  }, [user]);

  return { stats, loading, error };
}
