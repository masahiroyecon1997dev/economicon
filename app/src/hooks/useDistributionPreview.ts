import { getEconomiconAppAPI } from "@/api/endpoints";
import type {
  DistributionConfig,
  DistributionPreviewResult,
} from "@/api/model";
import { buildCaughtErrorMessage } from "@/lib/utils/apiError";
import { useCallback, useEffect, useRef, useState } from "react";

const DEBOUNCE_MS = 300;

type UseDistributionPreviewReturn = {
  loading: boolean;
  error: string | null;
  result: DistributionPreviewResult | null;
};

export const useDistributionPreview = (
  distribution: DistributionConfig | null,
): UseDistributionPreviewReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DistributionPreviewResult | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cancelledRef = useRef(false);

  const fetchPreview = useCallback(async (dist: DistributionConfig) => {
    cancelledRef.current = false;
    setLoading(true);
    setError(null);
    try {
      const response = await getEconomiconAppAPI().previewDistribution({
        distribution: dist,
      });
      if (!cancelledRef.current) {
        setResult(response.result);
      }
    } catch (e) {
      if (!cancelledRef.current) {
        setError(buildCaughtErrorMessage(e, "Preview failed"));
        setResult(null);
      }
    } finally {
      if (!cancelledRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (!distribution) {
      setResult(null);
      setError(null);
      setLoading(false);
      return;
    }

    cancelledRef.current = true;
    if (timerRef.current) clearTimeout(timerRef.current);

    timerRef.current = setTimeout(() => {
      void fetchPreview(distribution);
    }, DEBOUNCE_MS);

    return () => {
      cancelledRef.current = true;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [distribution, fetchPreview]);

  return { loading, error, result };
};
