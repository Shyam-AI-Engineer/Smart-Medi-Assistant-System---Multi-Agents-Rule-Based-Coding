"use client";

import { useEffect, useRef, useState } from "react";
import { Sparkles, Stethoscope, MessageSquarePlus, ShieldAlert } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { TypingDots } from "@/components/ui/Loader";
import { MessageBubble, type ChatBubbleMessage } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { useSendChat } from "@/hooks/useChat";
import { useMyPatientProfile } from "@/hooks/useVitals";
import { getApiErrorMessage } from "@/lib/api";

const SUGGESTIONS = [
  "What does a heart rate of 110 mean?",
  "Are my recent vitals trending in the right direction?",
  "What should I do if my SpO₂ drops below 92?",
  "Is ibuprofen safe to combine with my medications?",
];

function uid() {
  return Math.random().toString(36).slice(2);
}

export default function ChatPage() {
  const { data: profile } = useMyPatientProfile();
  const send = useSendChat();
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatBubbleMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, send.isPending]);

  async function handleSend(text?: string) {
    const content = (text ?? input).trim();
    if (!content) return;
    setInput("");
    const userMsg: ChatBubbleMessage = { id: uid(), role: "user", content };
    setMessages((m) => [...m, userMsg]);

    try {
      const res = await send.mutateAsync({
        message: content,
        patient_id: profile?.id,
      });
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          content: res.response,
          agent: res.agent_used,
          sources: res.sources,
        },
      ]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        {
          id: uid(),
          role: "assistant",
          content: getApiErrorMessage(err, "The AI service is temporarily unavailable."),
          error: true,
        },
      ]);
    }
  }

  function clearChat() {
    setMessages([]);
  }

  const empty = messages.length === 0;

  return (
    <div className="h-[calc(100vh-3.5rem)] lg:h-screen flex flex-col">
      <div className="container max-w-4xl pt-8 pb-4 shrink-0">
        <PageHeader
          title="AI Clinical Chat"
          description="Sourced answers grounded in your medical knowledge base."
          actions={
            !empty && (
              <Button variant="secondary" size="md" onClick={clearChat}>
                <MessageSquarePlus className="size-4" /> New chat
              </Button>
            )
          }
        />
      </div>

      <div
        ref={scrollRef}
        className="flex-1 min-h-0 overflow-y-auto"
      >
        <div className="container max-w-4xl py-6">
          {empty ? (
            <div className="py-12">
              <div className="flex items-center gap-3">
                <div className="size-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center">
                  <Stethoscope className="size-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-ink">How can I help today?</h2>
                  <p className="text-sm text-ink-muted">
                    Ask about symptoms, medications, vitals trends, or care guidance.
                  </p>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-3">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="text-left p-4 rounded-lg border border-border bg-bg-elevated hover:border-border-strong hover:shadow-card transition-all group"
                  >
                    <div className="flex items-start gap-2.5">
                      <Sparkles className="size-4 text-brand-500 mt-0.5 shrink-0" />
                      <span className="text-sm text-ink leading-relaxed group-hover:text-brand-700">
                        {s}
                      </span>
                    </div>
                  </button>
                ))}
              </div>

              <div className="mt-8 flex items-start gap-2.5 px-3 py-2.5 rounded-md bg-warning-50 border border-warning-100 text-xs text-warning-700">
                <ShieldAlert className="size-4 mt-0.5 shrink-0" />
                <span>
                  Information provided is for educational purposes and is not a substitute for
                  professional medical advice, diagnosis, or treatment.
                </span>
              </div>
            </div>
          ) : (
            <div className="space-y-5 py-2">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
              {send.isPending && (
                <div className="msg-enter flex gap-3">
                  <div className="size-8 shrink-0 rounded-full bg-bg-elevated border border-border flex items-center justify-center text-brand-700">
                    <Stethoscope className="size-4" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl rounded-tl-md bg-bg-elevated border border-border shadow-card">
                    <TypingDots />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="shrink-0 border-t border-border bg-bg-elevated/60 backdrop-blur">
        <div className="container max-w-4xl py-4">
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={() => handleSend()}
            disabled={send.isPending}
          />
          <p className="mt-2 text-center text-xs text-ink-subtle">
            AI responses can be inaccurate. Always verify with a clinician.
          </p>
        </div>
      </div>
    </div>
  );
}
