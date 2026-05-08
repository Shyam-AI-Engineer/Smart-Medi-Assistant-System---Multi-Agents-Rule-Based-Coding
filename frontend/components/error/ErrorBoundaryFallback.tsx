"use client";

import { useEffect } from "react";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryFallbackProps {
  error: Error & { digest?: string };
  reset: () => void;
  title?: string;
  description?: string;
  showDetails?: boolean;
}

export function ErrorBoundaryFallback({
  error,
  reset,
  title = "Something went wrong",
  description = "An unexpected error occurred. Please try again.",
  showDetails = false,
}: ErrorBoundaryFallbackProps) {
  useEffect(() => {
    // Log error to monitoring service (Sentry, etc) in production
    console.error("Error boundary caught:", error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-screen bg-bg">
      <div className="bg-white border border-border rounded-lg shadow-lg p-8 max-w-md w-full mx-4">
        <div className="flex justify-center mb-4">
          <AlertCircle className="w-12 h-12 text-red-500" />
        </div>

        <h2 className="text-xl font-semibold text-center text-ink mb-2">
          {title}
        </h2>

        <p className="text-center text-ink-secondary mb-6">
          {description}
        </p>

        {showDetails && error?.message && (
          <div className="bg-red-50 border border-red-200 rounded p-3 mb-6">
            <p className="text-sm text-red-800 font-mono break-words">
              {error.message}
            </p>
            {error.digest && (
              <p className="text-xs text-red-600 mt-1">
                Error ID: {error.digest}
              </p>
            )}
          </div>
        )}

        <div className="flex gap-3">
          <Button
            variant="outline"
            className="flex-1"
            onClick={() => window.location.href = "/"}
          >
            Home
          </Button>
          <Button
            className="flex-1"
            onClick={reset}
          >
            Try Again
          </Button>
        </div>
      </div>
    </div>
  );
}
