"use client";

import { ErrorBoundaryFallback } from "@/components/error/ErrorBoundaryFallback";

export default function AdminError({
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
      title="Admin Panel Error"
      description="An error occurred in the admin panel. Try again or contact support."
      showDetails={process.env.NODE_ENV === "development"}
    />
  );
}
