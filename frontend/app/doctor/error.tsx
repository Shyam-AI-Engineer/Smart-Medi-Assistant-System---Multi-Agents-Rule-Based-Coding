"use client";

import { ErrorBoundaryFallback } from "@/components/error/ErrorBoundaryFallback";

export default function DoctorError({
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
      title="Doctor Portal Error"
      description="An error occurred in the doctor portal. Try again or contact support."
      showDetails={process.env.NODE_ENV === "development"}
    />
  );
}
