import { ArrowUpRight, AlertTriangle, CheckCircle2, AlertCircle, Info } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import type { VitalsAnalysis } from "@/lib/api";

const STATUS_TONE: Record<string, { tone: "success" | "warning" | "danger" | "neutral"; label: string; Icon: any }> = {
  NORMAL: { tone: "success", label: "Normal", Icon: CheckCircle2 },
  MODERATE: { tone: "warning", label: "Moderate", Icon: Info },
  HIGH: { tone: "warning", label: "High", Icon: AlertCircle },
  CRITICAL: { tone: "danger", label: "Critical", Icon: AlertTriangle },
};

interface Props {
  analysis: VitalsAnalysis;
  trend?: "WORSENING" | "IMPROVING" | "STABLE";
}

export function AnalysisResult({ analysis, trend }: Props) {
  const status = STATUS_TONE[analysis.overall_status] || STATUS_TONE.NORMAL;
  const StatusIcon = status.Icon;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <CardTitle>Analysis result</CardTitle>
            <CardDescription>
              AI-driven assessment based on your latest measurements.
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {trend && (
              <Badge
                tone={trend === "WORSENING" ? "danger" : trend === "IMPROVING" ? "success" : "neutral"}
                dot
              >
                Trend: {trend.toLowerCase()}
              </Badge>
            )}
            <Badge tone={status.tone} dot>
              <StatusIcon className="size-3" /> {status.label}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall assessment */}
        <div>
          <p className="text-sm font-medium text-ink-muted">Overall assessment</p>
          <p className="mt-1.5 text-[15px] text-ink leading-relaxed">
            {analysis.overall_assessment}
          </p>
        </div>

        {/* Critical findings */}
        {analysis.critical_findings.length > 0 && (
          <div className="rounded-lg bg-danger-50 border border-danger-100 p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="size-4 text-danger-600" />
              <p className="text-sm font-medium text-danger-700">Critical findings</p>
            </div>
            <ul className="mt-2 space-y-1.5 text-sm text-danger-700 list-disc pl-5">
              {analysis.critical_findings.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Per-vital breakdown */}
        {analysis.vital_analyses.length > 0 && (
          <div>
            <p className="text-sm font-medium text-ink-muted mb-3">Per-vital breakdown</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {analysis.vital_analyses.map((v) => {
                const t = STATUS_TONE[v.status] || STATUS_TONE.NORMAL;
                const Icon = t.Icon;
                return (
                  <div
                    key={v.vital_type}
                    className="rounded-lg border border-border p-4 bg-bg-elevated"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium text-ink capitalize">
                        {v.vital_type.replace(/_/g, " ")}
                      </p>
                      <Badge tone={t.tone}>
                        <Icon className="size-3" /> {t.label}
                      </Badge>
                    </div>
                    <p className="mt-2 text-2xl font-semibold tracking-tight text-ink">
                      {v.value}
                      <span className="ml-1 text-sm font-normal text-ink-subtle">{v.unit}</span>
                    </p>
                    <p className="mt-2 text-xs text-ink-subtle">
                      Normal: {v.normal_range.min}–{v.normal_range.max} {v.unit}
                    </p>
                    {v.recommendation && (
                      <p className="mt-3 text-sm text-ink-muted leading-relaxed">
                        {v.recommendation}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {analysis.recommendations.length > 0 && (
          <div>
            <p className="text-sm font-medium text-ink-muted mb-2">Recommendations</p>
            <ul className="space-y-2">
              {analysis.recommendations.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink">
                  <ArrowUpRight className="size-4 mt-0.5 text-brand-500 shrink-0" />
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {analysis.should_escalate_to_triage && (
          <div className="rounded-lg bg-danger-50 border border-danger-100 p-4 flex items-start gap-3">
            <AlertTriangle className="size-5 text-danger-600 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-danger-700">
                Recommended to escalate to triage
              </p>
              <p className="mt-1 text-sm text-danger-700">
                Please contact your care provider or emergency services if symptoms persist.
              </p>
            </div>
          </div>
        )}

        {analysis.disclaimer && (
          <p className="text-xs text-ink-subtle border-t border-border pt-4">
            {analysis.disclaimer}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
