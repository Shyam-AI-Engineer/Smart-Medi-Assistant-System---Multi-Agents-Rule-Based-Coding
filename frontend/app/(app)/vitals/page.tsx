"use client";

import { useState } from "react";
import { AlertCircle } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Loader } from "@/components/ui/Loader";
import { VitalsForm, type VitalsFormValues } from "@/components/vitals/VitalsForm";
import { AnalysisResult } from "@/components/vitals/AnalysisResult";
import { RealtimeVitalsWidget } from "@/components/vitals/RealtimeVitalsWidget";
import { useMyPatientProfile, useStoreVitals, useAnalyzeVitals } from "@/hooks/useVitals";
import { getApiErrorMessage, type VitalsAnalysis } from "@/lib/api";

export default function VitalsPage() {
  const { data: profile, isLoading: profileLoading } = useMyPatientProfile();
  const store = useStoreVitals(profile?.id);
  const analyze = useAnalyzeVitals();

  const [analysis, setAnalysis] = useState<VitalsAnalysis | null>(null);
  const [trend, setTrend] = useState<"WORSENING" | "IMPROVING" | "STABLE" | undefined>();
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(values: VitalsFormValues) {
    setError(null);
    setAnalysis(null);
    setTrend(undefined);

    try {
      if (profile?.id) {
        // Persist + analyze + trend
        const res = await store.mutateAsync(values);
        setAnalysis(res.analysis);
        setTrend(res.trend);
      } else {
        // Stateless analysis only (no patient profile)
        const res = await analyze.mutateAsync(values);
        setAnalysis(res);
      }
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not analyze vitals."));
    }
  }

  const submitting = store.isPending || analyze.isPending;

  return (
    <div className="container py-8 max-w-4xl">
      <PageHeader
        title="Vitals"
        description={
          profile?.id
            ? "Record measurements to track trends and get instant AI analysis."
            : "Try the analyzer — your readings will not be stored."
        }
      />

      {profileLoading ? (
        <div className="py-24">
          <Loader label="Loading…" />
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          {profile?.id && <RealtimeVitalsWidget patientId={profile.id} />}
          <VitalsForm onSubmit={onSubmit} loading={submitting} />

          {error && (
            <div className="flex items-start gap-2 px-4 py-3 rounded-md bg-danger-50 border border-danger-100 text-sm text-danger-700">
              <AlertCircle className="size-4 mt-0.5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {analysis && <AnalysisResult analysis={analysis} trend={trend} />}
        </div>
      )}
    </div>
  );
}
