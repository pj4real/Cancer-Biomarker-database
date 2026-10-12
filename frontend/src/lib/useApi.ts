import { useEffect, useState } from "react";
import { apiGet, type QueryValue } from "../api/client";

export interface ApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/** Fetch `path` whenever it or its params change; aborts stale requests. */
export function useApi<T>(path: string | null, params: Record<string, QueryValue> = {}): ApiState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);
  const key = JSON.stringify(params);

  useEffect(() => {
    if (path === null) {
      setLoading(false);
      return;
    }
    const ctrl = new AbortController();
    setLoading(true);
    setError(null);
    apiGet<T>(path, JSON.parse(key), ctrl.signal)
      .then((d) => setData(d))
      .catch((e: Error) => {
        if (e.name !== "AbortError") setError(e.message || "Could not load data");
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setLoading(false);
      });
    return () => ctrl.abort();
  }, [path, key, tick]);

  return { data, loading, error, reload: () => setTick((t) => t + 1) };
}
