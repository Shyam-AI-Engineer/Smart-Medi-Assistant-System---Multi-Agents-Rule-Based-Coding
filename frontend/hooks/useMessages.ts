"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints } from "@/lib/api";

// ── Patient hooks ──────────────────────────────────────────────────────────

export function useMessages() {
  return useQuery({
    queryKey: ["messages"],
    queryFn: () => endpoints.getMessages(),
    staleTime: 30_000,
    refetchInterval: 120_000,
  });
}

export function useMarkMessageRead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => endpoints.markMessageRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["messages"] }),
  });
}

export function useReplyToDoctor() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ doctorUserId, body }: { doctorUserId: string; body: string }) =>
      endpoints.replyToDoctor(doctorUserId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["messages"] }),
  });
}

// ── Doctor hooks ───────────────────────────────────────────────────────────

export function useDoctorMessages(patientId: string | null) {
  return useQuery({
    queryKey: ["doctor-messages", patientId],
    queryFn: () => endpoints.getDoctorMessages(patientId!),
    enabled: Boolean(patientId),
    refetchInterval: 30_000,
  });
}

export function useSendDoctorMessage() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ patientId, body }: { patientId: string; body: string }) =>
      endpoints.sendDoctorMessage(patientId, body),
    onSuccess: (_, { patientId }) => {
      qc.invalidateQueries({ queryKey: ["doctor-messages", patientId] });
    },
  });
}
