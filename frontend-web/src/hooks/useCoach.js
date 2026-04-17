import { useState } from "react";
import { analyzeComposition } from "../api/coach";

export default function useCoach() {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const analyze = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      const data = await analyzeComposition(payload);
      setResult(data);
    } catch (e) {
      setError(e.response?.data?.error ?? e.message);
    } finally {
      setLoading(false);
    }
  };

  return { result, loading, error, analyze };
}
