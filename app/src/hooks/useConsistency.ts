import { getEconomiconAppAPI } from "@/api/endpoints";
import type { ConsistencyRequestBody, ConsistencyResult } from "@/api/model";
import { buildCaughtErrorMessage } from "@/lib/utils/apiError";
import { useCallback, useEffect, useRef, useState } from "react";

const DEBOUNCE_MS = 300;

type UseConsistencyReturn = {
  loading: boolean;
  error: string | null;
  result: ConsistencyResult | null;
};

export const useConsistency = (
  params: ConsistencyRequestBody,
): UseConsistencyReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConsistencyResult | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelledRef = useRef(false);

  const fetchResult = useCallback(async (body: ConsistencyRequestBody) => {
    cancelledRef.current = false;
    setLoading(true);
    setError(null);
    try {
      const response = await getEconomiconAppAPI().consistency(body);
      if (!cancelledRef.current) {
        setResult(response.result);
      }
    } catch (e) {
      if (!cancelledRef.current) {
        setError(buildCaughtErrorMessage(e, "Simulation failed"));
        setResult(null);
      }
    } finally {
      if (!cancelledRef.current) {
        setLoading(false);
      }
    }
  }, []);

  const paramsJson = JSON.stringify(params);

  useEffect(() => {
    cancelledRef.current = true;
    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(() => {
      void fetchResult(JSON.parse(paramsJson) as ConsistencyRequestBody);
    }, DEBOUNCE_MS);

    return () => {
      cancelledRef.current = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [paramsJson, fetchResult]);

  return { loading, error, result };
};
