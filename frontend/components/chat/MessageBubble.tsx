import { Stethoscope, User } from "lucide-react";
import { cn } from "@/lib/cn";
import { Badge } from "@/components/ui/Badge";

export interface ChatBubbleMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  agent?: string;
  sources?: { file: string; relevance?: string }[];
  confidence_score?: number;
  error?: boolean;
}

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
            "px-4 py-2.5 rounded-2xl text-[15px] leading-relaxed whitespace-pre-wrap break-words",
            isUser
              ? "bg-brand-600 text-white rounded-tr-md"
              : "bg-bg-elevated border border-border text-ink rounded-tl-md shadow-card",
            message.error && "border-danger-200 bg-danger-50 text-danger-700",
          )}
        >
          {message.content}
        </div>

        {!isUser && (message.agent || message.sources?.length || message.confidence_score !== undefined) && (
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
          </div>
        )}
      </div>
    </div>
  );
}
