"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints, type MedicationPayload } from "@/lib/api";

export function useMedications() {
  return useQuery({
    queryKey: ["medications"],
    queryFn: () => endpoints.listMedications(),
  });
}

export function useAddMedication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: MedicationPayload) => endpoints.addMedication(payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["medications"] }),
  });
}

export function useDeleteMedication() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.deleteMedication(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["medications"] }),
  });
}

export function useCheckInteractions() {
  return useQuery({
    queryKey: ["medication-interactions"],
    queryFn: () => endpoints.checkInteractions(),
    enabled: false, // only run when manually triggered
  });
}
