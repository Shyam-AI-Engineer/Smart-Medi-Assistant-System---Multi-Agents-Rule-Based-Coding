import { Loader2 } from "lucide-react";
import { cn } from "@/lib/cn";

interface LoaderProps {
  size?: "sm" | "md" | "lg";
  label?: string;
  className?: string;
}

const sizes = {
  sm: "size-4",
  md: "size-6",
  lg: "size-8",
};

export function Loader({ size = "md", label, className }: LoaderProps) {
  return (
    <div className={cn("flex items-center justify-center gap-3 text-ink-muted", className)}>
      <Loader2 className={cn("animate-spin", sizes[size])} />
      {label && <span className="text-sm">{label}</span>}
    </div>
  );
}

export function FullPageLoader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <Loader size="lg" label={label} />
    </div>
  );
}

export function TypingDots() {
  return (
    <div className="inline-flex items-center gap-1">
      <span className="size-1.5 rounded-full bg-ink-subtle animate-pulse-soft [animation-delay:-0.32s]" />
      <span className="size-1.5 rounded-full bg-ink-subtle animate-pulse-soft [animation-delay:-0.16s]" />
      <span className="size-1.5 rounded-full bg-ink-subtle animate-pulse-soft" />
    </div>
  );
}
