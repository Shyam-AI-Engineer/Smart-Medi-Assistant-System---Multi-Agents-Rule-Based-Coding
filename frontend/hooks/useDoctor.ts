"use client";

import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/api";

export function useDoctorPatients(limit = 20, offset = 0) {
  return useQuery({
    queryKey: ["doctor-patients", limit, offset],
    queryFn: () => endpoints.doctorPatients(limit, offset),
  });
}

export function usePatientDetail(patientId: string | undefined, vitalsLimit = 30, chatLimit = 20) {
  return useQuery({
    queryKey: ["patient-detail", patientId, vitalsLimit, chatLimit],
    queryFn: () => endpoints.patientDetail(patientId!, vitalsLimit, chatLimit),
    enabled: !!patientId,
  });
}
