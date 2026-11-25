import { useCallback, useEffect, useRef, useState } from "react";

const INTERVAL_MS = 15_000;

/** Carga datos y los refresca cada 15 s mientras la pestaña esté visible. */
export function usePolling<T>(load: () => Promise<T>, key: unknown) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);
  const loadRef = useRef(load);
  const requestRef = useRef(0);
  loadRef.current = load;

  const refresh = useCallback(async () => {
    const request = ++requestRef.current;
    try {
      const result = await loadRef.current();
      // Si otra consulta empezó después, esta respuesta ya es vieja.
      if (request !== requestRef.current) return;
      setData(result);
      setError(null);
      setUpdatedAt(new Date());
    } catch (reason) {
      if (request === requestRef.current) setError(reason as Error);
    }
  }, []);

  useEffect(() => {
    setData(null);
    setError(null);
    void refresh();

    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh();
    }, INTERVAL_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") void refresh();
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      requestRef.current += 1;
    };
  }, [key, refresh]);

  return { data, error, updatedAt, refresh };
}
