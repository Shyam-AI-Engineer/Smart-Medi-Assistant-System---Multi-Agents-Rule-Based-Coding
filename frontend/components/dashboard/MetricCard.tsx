import type { ReactNode } from "react";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/cn";

type Trend = "improving" | "worsening" | "stable" | "none";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: Trend;
  icon?: ReactNode;
  hint?: string;
  className?: string;
}

const trendBadge: Record<Trend, { tone: "success" | "danger" | "neutral"; label: string; Icon: any }> = {
  improving: { tone: "success", label: "Improving", Icon: TrendingDown },
  worsening: { tone: "danger", label: "Worsening", Icon: TrendingUp },
  stable: { tone: "neutral", label: "Stable", Icon: Minus },
  none: { tone: "neutral", label: "—", Icon: Minus },
};

export function MetricCard({
  label,
  value,
  unit,
  trend = "none",
  icon,
  hint,
  className,
}: MetricCardProps) {
  const t = trendBadge[trend];
  const TrendIcon = t.Icon;
  return (
    <Card className={cn("p-5", className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-ink-muted">{label}</span>
        {icon && (
          <div className="size-8 rounded-md bg-bg-subtle text-ink-muted flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline gap-1.5">
        <span className="text-[28px] font-semibold tracking-tight text-ink leading-none">
          {value}
        </span>
        {unit && <span className="text-sm text-ink-subtle">{unit}</span>}
      </div>
      <div className="mt-4 flex items-center justify-between">
        {trend !== "none" ? (
          <Badge tone={t.tone} dot>
            <TrendIcon className="size-3" /> {t.label}
          </Badge>
        ) : (
          <span className="text-xs text-ink-subtle">No trend yet</span>
        )}
        {hint && <span className="text-xs text-ink-subtle">{hint}</span>}
      </div>
    </Card>
  );
}
