"use client";

import { useCallback, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { endpoints, sendChatStream, type SendChatPayload, type ChatStreamMeta } from "@/lib/api";

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
      queryClient.invalidateQueries({
        queryKey: ["chat-history", variables.patient_id],
        exact: false,
      });
    },
  });
}

export function useStreamChat() {
  const queryClient = useQueryClient();
  const [isStreaming, setIsStreaming] = useState(false);

  const stream = useCallback(
    async (
      payload: SendChatPayload,
      onToken: (token: string) => void,
      onDone: (meta: ChatStreamMeta) => void,
      onError: (msg: string) => void,
    ) => {
      setIsStreaming(true);
      try {
        await sendChatStream(
          payload,
          onToken,
          (meta) => {
            queryClient.invalidateQueries({
              queryKey: ["chat-history", payload.patient_id],
              exact: false,
            });
            onDone(meta);
          },
          onError,
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [queryClient],
  );

  return { stream, isStreaming };
}

export function useSubmitFeedback() {
  return useMutation({
    mutationFn: ({
      chatId,
      feedback,
    }: {
      chatId: string;
      feedback: "thumbs_up" | "thumbs_down";
    }) => endpoints.submitFeedback(chatId, feedback),
  });
}
