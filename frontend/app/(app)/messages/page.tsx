"use client";

import { useState, useMemo } from "react";
import { Inbox, Send, ChevronLeft, User } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { useMessages, useMarkMessageRead, useReplyToDoctor } from "@/hooks/useMessages";
import { cn } from "@/lib/cn";
import type { DoctorMessage } from "@/lib/api";

// ── Derived type for a thread (grouped by doctor) ──────────────────────────

interface Thread {
  doctorUserId: string;
  doctorName: string;
  messages: DoctorMessage[];
  unreadCount: number;
  lastMessageAt: string;
  lastPreview: string;
}

function buildThreads(items: DoctorMessage[]): Thread[] {
  const map = new Map<string, Thread>();
  // items arrive newest-first; we want newest last within a thread
  const ordered = [...items].reverse();
  for (const m of ordered) {
    if (!map.has(m.doctor_user_id)) {
      map.set(m.doctor_user_id, {
        doctorUserId: m.doctor_user_id,
        doctorName: m.doctor_name,
        messages: [],
        unreadCount: 0,
        lastMessageAt: m.created_at,
        lastPreview: "",
      });
    }
    const t = map.get(m.doctor_user_id)!;
    t.messages.push(m);
    t.lastMessageAt = m.created_at;
    t.lastPreview = m.body.slice(0, 60) + (m.body.length > 60 ? "…" : "");
    if (m.sender_role === "doctor" && !m.is_read) t.unreadCount++;
  }
  // Sort threads: newest last message first
  return [...map.values()].sort(
    (a, b) => new Date(b.lastMessageAt).getTime() - new Date(a.lastMessageAt).getTime(),
  );
}

function formatTime(iso: string) {
  const d = new Date(iso);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) {
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

// ── Thread list item ───────────────────────────────────────────────────────

function ThreadRow({
  thread,
  selected,
  onClick,
}: {
  thread: Thread;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left px-4 py-3 border-b border-border transition-colors",
        selected ? "bg-brand-50" : "hover:bg-bg-subtle",
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <span className="text-sm font-semibold text-ink truncate">{thread.doctorName}</span>
        <span className="text-xs text-ink-subtle shrink-0">{formatTime(thread.lastMessageAt)}</span>
      </div>
      <div className="flex items-center gap-2">
        <p className="text-xs text-ink-muted truncate flex-1">{thread.lastPreview}</p>
        {thread.unreadCount > 0 && (
          <Badge tone="brand" className="shrink-0">
            {thread.unreadCount}
          </Badge>
        )}
      </div>
    </button>
  );
}

// ── Thread view ────────────────────────────────────────────────────────────

function ThreadView({ thread }: { thread: Thread }) {
  const [replyText, setReplyText] = useState("");
  const markRead = useMarkMessageRead();
  const reply = useReplyToDoctor();

  // Mark unread doctor messages as read when thread opens
  useMemo(() => {
    for (const m of thread.messages) {
      if (m.sender_role === "doctor" && !m.is_read) {
        markRead.mutate(m.id);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [thread.doctorUserId]);

  async function handleReply() {
    const text = replyText.trim();
    if (!text) return;
    await reply.mutateAsync({ doctorUserId: thread.doctorUserId, body: text });
    setReplyText("");
  }

  return (
    <div className="flex flex-col h-full">
      {/* Thread header */}
      <div className="px-5 py-3 border-b border-border bg-bg-elevated flex items-center gap-3">
        <div className="size-8 rounded-full bg-brand-100 text-brand-700 text-sm font-semibold flex items-center justify-center">
          {thread.doctorName.charAt(0).toUpperCase()}
        </div>
        <div>
          <p className="text-sm font-semibold text-ink">{thread.doctorName}</p>
          <p className="text-xs text-ink-subtle">Care team</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {thread.messages.map((m) => {
          const isDoctor = m.sender_role === "doctor";
          return (
            <div
              key={m.id}
              className={cn("flex", isDoctor ? "justify-start" : "justify-end")}
            >
              <div
                className={cn(
                  "max-w-[75%] rounded-xl px-4 py-2.5 text-sm leading-relaxed",
                  isDoctor
                    ? "bg-bg-subtle text-ink rounded-tl-sm"
                    : "bg-brand-500 text-white rounded-tr-sm",
                )}
              >
                <p>{m.body}</p>
                <p
                  className={cn(
                    "text-[10px] mt-1",
                    isDoctor ? "text-ink-subtle" : "text-brand-100",
                  )}
                >
                  {formatTime(m.created_at)}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Reply box */}
      <div className="p-4 border-t border-border bg-bg-elevated">
        <div className="flex gap-2">
          <textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Reply to your doctor…"
            rows={2}
            className={cn(
              "flex-1 px-3 py-2 rounded-lg border border-border bg-bg-elevated",
              "text-sm text-ink placeholder:text-ink-subtle resize-none",
              "outline-none focus:border-brand-500 focus:shadow-focus transition-shadow",
            )}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleReply();
            }}
          />
          <Button
            onClick={handleReply}
            disabled={!replyText.trim() || reply.isPending}
            loading={reply.isPending}
            className="self-end"
          >
            <Send className="size-4" />
          </Button>
        </div>
        <p className="text-[10px] text-ink-subtle mt-1.5">⌘ Enter to send</p>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function MessagesPage() {
  const { data, isLoading } = useMessages();
  const [selectedDoctorId, setSelectedDoctorId] = useState<string | null>(null);

  const threads = useMemo(
    () => buildThreads(data?.items ?? []),
    [data],
  );

  const selectedThread = threads.find((t) => t.doctorUserId === selectedDoctorId) ?? null;

  // On mobile, when a thread is selected show it full-screen
  const showThread = Boolean(selectedThread);

  if (isLoading) {
    return (
      <div className="flex justify-center py-16">
        <Loader size="lg" label="Loading messages…" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Messages"
        description="Direct messages from your care team"
      />

      {threads.length === 0 ? (
        <EmptyState
          icon={<Inbox className="size-6 text-brand-500" />}
          title="No messages yet"
          description="Your doctor can send you notes, follow-ups, and care instructions here."
        />
      ) : (
        <div className="rounded-xl border border-border bg-bg-elevated overflow-hidden flex h-[calc(100vh-14rem)] shadow-card">
          {/* Thread list */}
          <aside
            className={cn(
              "w-72 shrink-0 border-r border-border flex flex-col",
              showThread && "hidden sm:flex",
            )}
          >
            <div className="px-4 py-3 border-b border-border">
              <p className="text-xs font-semibold text-ink-muted uppercase tracking-wide">
                Conversations
              </p>
            </div>
            <div className="flex-1 overflow-y-auto">
              {threads.map((t) => (
                <ThreadRow
                  key={t.doctorUserId}
                  thread={t}
                  selected={selectedDoctorId === t.doctorUserId}
                  onClick={() => setSelectedDoctorId(t.doctorUserId)}
                />
              ))}
            </div>
          </aside>

          {/* Thread view */}
          <main className="flex-1 min-w-0 flex flex-col">
            {selectedThread ? (
              <>
                {/* Mobile back button */}
                <button
                  className="sm:hidden flex items-center gap-1 px-4 py-2 text-sm text-brand-600 border-b border-border"
                  onClick={() => setSelectedDoctorId(null)}
                >
                  <ChevronLeft className="size-4" /> Back
                </button>
                <ThreadView thread={selectedThread} />
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-ink-subtle">
                <div className="text-center space-y-2">
                  <User className="size-8 mx-auto text-ink-subtle" />
                  <p className="text-sm">Select a conversation</p>
                </div>
              </div>
            )}
          </main>
        </div>
      )}
    </div>
  );
}
