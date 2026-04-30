"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadReport, endpoints } from "@/lib/api";

export function useReports(patientId: string | undefined) {
  return useQuery({
    queryKey: ["reports", patientId],
    queryFn: () => endpoints.listReports(),
    enabled: !!patientId,
  });
}

export function useUploadReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadReport(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
}

export function useDeleteReport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reportId: string) => endpoints.deleteReport(reportId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["reports"] }),
  });
}
