"use client";

import { ErrorBoundaryFallback } from "@/components/error/ErrorBoundaryFallback";

export default function RootError({
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
      title="Application Error"
      description="The application encountered an unexpected error. Our team has been notified."
      showDetails={process.env.NODE_ENV === "development"}
    />
  );
}
