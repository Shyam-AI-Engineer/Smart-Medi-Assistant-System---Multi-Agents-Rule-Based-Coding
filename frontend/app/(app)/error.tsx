"use client";

import { ErrorBoundaryFallback } from "@/components/error/ErrorBoundaryFallback";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorBoundaryFallback
      error={error}
      reset={reset}
      title="Page Error"
      description="Something went wrong on this page. Try refreshing or go back to dashboard."
      showDetails={process.env.NODE_ENV === "development"}
    />
  );
}
