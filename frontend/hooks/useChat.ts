"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints, type SendChatPayload } from "@/lib/api";

export function useChatHistory(patientId: string | undefined, limit = 50) {
  return useQuery({
    queryKey: ["chat-history", patientId, limit],
    queryFn: () => endpoints.chatHistory(patientId!, limit, 0),
    enabled: !!patientId,
  });
}

export function useSendChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SendChatPayload) => endpoints.sendChat(payload),
    onSuccess: (_, variables) => {
      const patientId = variables.patient_id;
      if (patientId) {
        // Invalidate the specific chat history query for this patient
        queryClient.invalidateQueries({
          queryKey: ["chat-history", patientId],
          exact: false, // Match any limit parameter
        });
      }
    },
  });
}
