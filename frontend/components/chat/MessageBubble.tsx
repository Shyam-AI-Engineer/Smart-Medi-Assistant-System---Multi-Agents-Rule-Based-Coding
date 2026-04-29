"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Stethoscope, User, ThumbsUp, ThumbsDown } from "lucide-react";
import { cn } from "@/lib/cn";
import { Badge } from "@/components/ui/Badge";

export interface ChatBubbleMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  sources?: { file: string; relevance?: string }[];
  confidence_score?: number;
  feedback?: "thumbs_up" | "thumbs_down" | null;
  error?: boolean;
  isStreaming?: boolean;
  onFeedback?: (id: string, value: "thumbs_up" | "thumbs_down") => void;
}

const mdComponents = {
  p: ({ children }: React.PropsWithChildren) => (
    <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
  ),
  ul: ({ children }: React.PropsWithChildren) => (
    <ul className="mb-2 ml-4 list-disc space-y-0.5 last:mb-0">{children}</ul>
  ),
  ol: ({ children }: React.PropsWithChildren) => (
    <ol className="mb-2 ml-4 list-decimal space-y-0.5 last:mb-0">{children}</ol>
  ),
  li: ({ children }: React.PropsWithChildren) => (
    <li className="leading-relaxed">{children}</li>
  ),
  strong: ({ children }: React.PropsWithChildren) => (
    <strong className="font-semibold">{children}</strong>
  ),
  h1: ({ children }: React.PropsWithChildren) => (
    <h1 className="mb-1 text-base font-semibold">{children}</h1>
  ),
  h2: ({ children }: React.PropsWithChildren) => (
    <h2 className="mb-1 text-sm font-semibold">{children}</h2>
  ),
  h3: ({ children }: React.PropsWithChildren) => (
    <h3 className="mb-1 text-sm font-semibold">{children}</h3>
  ),
  code: ({ children }: React.PropsWithChildren) => (
    <code className="rounded bg-bg-subtle px-1 py-0.5 font-mono text-xs">{children}</code>
  ),
  blockquote: ({ children }: React.PropsWithChildren) => (
    <blockquote className="my-1 border-l-2 border-border pl-3 text-ink-muted italic">
      {children}
    </blockquote>
  ),
};

export function MessageBubble({ message }: { message: ChatBubbleMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("msg-enter flex gap-3 group", isUser && "flex-row-reverse")}>
      <div
        className={cn(
          "size-8 shrink-0 rounded-full flex items-center justify-center text-sm font-medium",
          isUser
            ? "bg-brand-600 text-white"
            : "bg-bg-elevated border border-border text-brand-700",
        )}
      >
        {isUser ? <User className="size-4" /> : <Stethoscope className="size-4" />}
      </div>
      <div className={cn("max-w-[78%] min-w-0", isUser && "items-end")}>
        <div
          className={cn(
            "px-4 py-2.5 rounded-2xl text-[15px] leading-relaxed break-words",
            isUser
              ? "bg-brand-600 text-white rounded-tr-md whitespace-pre-wrap"
              : "bg-bg-elevated border border-border text-ink rounded-tl-md shadow-card",
            message.error && "border-danger-200 bg-danger-50 text-danger-700",
          )}
        >
          {isUser ? (
            message.content
          ) : (
            <div className="prose-sm">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={mdComponents}
              >
                {message.content}
              </ReactMarkdown>
              {message.isStreaming && (
                <span className="inline-block w-[2px] h-[1em] bg-current opacity-70 animate-pulse ml-0.5 align-middle" />
              )}
            </div>
          )}
        </div>

        {!isUser && !message.isStreaming && (message.agent || message.sources?.length || message.confidence_score !== undefined || message.onFeedback) && (
          <div className="mt-2 flex flex-wrap items-center gap-1.5">
            {message.agent && (
              <Badge tone="brand">{message.agent}</Badge>
            )}
            {message.confidence_score !== undefined && (
              <span className={cn(
                "text-xs font-medium",
                message.confidence_score >= 0.8 ? "text-success-600" :
                message.confidence_score >= 0.5 ? "text-warning-600" :
                "text-danger-600"
              )}>
                {message.confidence_score >= 0.8 ? "High" :
                 message.confidence_score >= 0.5 ? "Medium" : "Low"} confidence
              </span>
            )}
            {message.sources?.slice(0, 3).map((src, i) => (
              <Badge key={i} tone="neutral">
                {src.file}
                {src.relevance && (
                  <span className="ml-1 text-ink-subtle">· {src.relevance}</span>
                )}
              </Badge>
            ))}
            {!message.error && message.onFeedback && (
              <div className="ml-auto flex items-center gap-0.5">
                <button
                  onClick={() => message.onFeedback!(message.id, "thumbs_up")}
                  className={cn(
                    "p-1 rounded transition-colors",
                    message.feedback === "thumbs_up"
                      ? "text-success-600"
                      : "text-ink-subtle hover:text-ink"
                  )}
                  title="Helpful"
                >
                  <ThumbsUp className="size-3.5" />
                </button>
                <button
                  onClick={() => message.onFeedback!(message.id, "thumbs_down")}
                  className={cn(
                    "p-1 rounded transition-colors",
                    message.feedback === "thumbs_down"
                      ? "text-danger-600"
                      : "text-ink-subtle hover:text-ink"
                  )}
                  title="Not helpful"
                >
                  <ThumbsDown className="size-3.5" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
