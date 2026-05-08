"use client";

import { ErrorBoundaryFallback } from "@/components/error/ErrorBoundaryFallback";

export default function LoginError({
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
      title="Login Error"
      description="An error occurred during login. Please try again."
      showDetails={process.env.NODE_ENV === "development"}
    />
  );
}
