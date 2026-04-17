import { useState } from "react";
import { getProfile, syncProfile } from "../api/profiles";

export default function useProfile() {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const load = async (battletag) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProfile(battletag);
      setProfile(data);
    } catch (e) {
      setError(e.response?.data?.error ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  const sync = async (battletag) => {
    setLoading(true);
    setError(null);
    try {
      const data = await syncProfile(battletag);
      setProfile(data);
    } catch (e) {
      setError(e.response?.data?.error ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  return { profile, loading, error, load, sync };
}
