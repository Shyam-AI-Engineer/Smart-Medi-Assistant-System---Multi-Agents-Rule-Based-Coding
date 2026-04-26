import { cn } from "@/lib/cn";

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative size-7 rounded-md bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center shadow-sm">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          className="size-4 text-white"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 4v16M4 12h16" />
        </svg>
      </div>
      <span className="text-[15px] font-semibold tracking-tight text-ink">
        Medi<span className="text-brand-600">Assist</span>
      </span>
    </div>
  );
}
