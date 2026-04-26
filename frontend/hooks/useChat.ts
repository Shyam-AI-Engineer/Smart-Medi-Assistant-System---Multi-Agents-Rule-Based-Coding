"use client";

import { useMutation } from "@tanstack/react-query";
import { endpoints, type SendChatPayload } from "@/lib/api";

export function useSendChat() {
  return useMutation({
    mutationFn: (payload: SendChatPayload) => endpoints.sendChat(payload),
  });
}
