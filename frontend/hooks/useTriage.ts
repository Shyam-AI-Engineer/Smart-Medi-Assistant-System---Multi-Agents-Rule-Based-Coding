"use client";

import { useState, useCallback } from "react";
import { endpoints, type TriageResponse, getApiErrorMessage } from "@/lib/api";

export interface UseTriageReturn {
  result: TriageResponse | null;
  isLoading: boolean;
  error: string | null;
  assess: (symptoms: string) => Promise<void>;
  reset: () => void;
}

export function useTriage(): UseTriageReturn {
  const [result, setResult] = useState<TriageResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assess = useCallback(async (symptoms: string) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await endpoints.assessSymptoms(symptoms);
      setResult(data);
    } catch (err) {
      setError(getApiErrorMessage(err, "Assessment failed. Please try again."));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, isLoading, error, assess, reset };
}
