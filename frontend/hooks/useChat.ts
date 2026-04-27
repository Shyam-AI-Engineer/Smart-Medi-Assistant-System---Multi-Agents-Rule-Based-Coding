"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { endpoints, type SendChatPayload } from "@/lib/api";

export function useChatHistory(patientId: string | undefined, limit = 50) {
  return useQuery({
    queryKey: ["chat-history", patientId, limit],
    queryFn: () => endpoints.chatHistory(patientId!, limit, 0),
    enabled: !!patientId,
  });
}

export function useSendChat() {
  return useMutation({
    mutationFn: (payload: SendChatPayload) => endpoints.sendChat(payload),
  });
}
