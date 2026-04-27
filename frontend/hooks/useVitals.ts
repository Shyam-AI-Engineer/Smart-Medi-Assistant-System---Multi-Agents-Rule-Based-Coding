"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { endpoints, type VitalRecord, type VitalsAnalysis, type PatientProfile } from "@/lib/api";

export function useVitalsHistory(patientId: string | undefined, limit = 30) {
  return useQuery({
    queryKey: ["vitals-history", patientId, limit],
    queryFn: () => endpoints.vitalsHistory(patientId!, limit, 0),
    enabled: Boolean(patientId),
  });
}

export function useStoreVitals(patientId: string | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<VitalRecord>) =>
      endpoints.storeVitals({ ...payload, patient_id: patientId! }),
    onSuccess: () => {
      if (patientId) {
        qc.invalidateQueries({ queryKey: ["vitals-history", patientId] });
      }
    },
  });
}

export function useAnalyzeVitals() {
  return useMutation<VitalsAnalysis, Error, Partial<VitalRecord>>({
    mutationFn: (payload) => endpoints.analyzeVitals(payload),
  });
}

export function useMyPatientProfile() {
  return useQuery({
    queryKey: ["patient-profile", "me"],
    queryFn: () => endpoints.myProfile(),
    retry: 0,
  });
}

export function useUpdateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Partial<PatientProfile>) =>
      endpoints.updateProfile(payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["patient-profile", "me"] });
    },
  });
}
