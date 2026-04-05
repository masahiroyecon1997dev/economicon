import { useCallback, useState } from "react";
import { getEconomiconAppAPI } from "../api/endpoints";
import type { OutputResultRequest } from "../api/model/outputResultRequest";
import { extractApiErrorMessage } from "../lib/utils/apiError";

type UseOutputResultReturnType = {
  content: string | null;
  isLoading: boolean;
  error: string | null;
  fetchOutput: (request: OutputResultRequest) => Promise<void>;
};

export const useOutputResult = (): UseOutputResultReturnType => {
  const [content, setContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchOutput = useCallback(async (request: OutputResultRequest) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getEconomiconAppAPI().outputResult(request);
      if (response.code === "OK" && response.result) {
        setContent(response.result.content);
      } else {
        setError("error");
      }
    } catch (err) {
      setError(extractApiErrorMessage(err, "error"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { content, isLoading, error, fetchOutput };
};
