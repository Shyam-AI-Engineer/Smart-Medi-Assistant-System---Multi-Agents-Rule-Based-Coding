"use client";

import { useState } from "react";
import {
  AlertTriangle,
  Phone,
  CheckCircle,
  Clock,
  ShieldAlert,
  Loader2,
  ArrowRight,
  RotateCcw,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { useTriage } from "@/hooks/useTriage";
import { cn } from "@/lib/cn";
import type { TriageResponse } from "@/lib/api";

const URGENCY_CONFIG = {
  critical: {
    label: "CRITICAL",
    bg: "bg-danger-50",
    border: "border-danger-300",
    text: "text-danger-700",
    badge: "danger" as const,
    icon: AlertTriangle,
  },
  urgent: {
    label: "URGENT",
    bg: "bg-warning-50",
    border: "border-warning-300",
    text: "text-warning-700",
    badge: "warning" as const,
    icon: Clock,
  },
  moderate: {
    label: "MODERATE",
    bg: "bg-brand-50",
    border: "border-brand-200",
    text: "text-brand-700",
    badge: "brand" as const,
    icon: Clock,
  },
  "self-care": {
    label: "SELF-CARE",
    bg: "bg-success-50",
    border: "border-success-200",
    text: "text-success-700",
    badge: "success" as const,
    icon: CheckCircle,
  },
};

function getUrgencyConfig(level: string) {
  return URGENCY_CONFIG[level as keyof typeof URGENCY_CONFIG] ?? URGENCY_CONFIG.moderate;
}

function SeverityBar({ score }: { score: number }) {
  const pct = Math.round((score / 10) * 100);
  const color =
    score >= 8 ? "bg-danger-500" : score >= 6 ? "bg-warning-500" : score >= 4 ? "bg-brand-500" : "bg-success-500";
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-ink-muted">
        <span>Severity score</span>
        <span className="font-medium text-ink">{score}/10</span>
      </div>
      <div className="h-2 rounded-full bg-bg-subtle overflow-hidden">
        <div className={cn("h-full rounded-full transition-all", color)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function TriageResult({ result, onReset }: { result: TriageResponse; onReset: () => void }) {
  const cfg = getUrgencyConfig(result.urgency_level);
  const UrgencyIcon = cfg.icon;

  return (
    <div className="space-y-4">
      {/* Urgency banner */}
      <div className={cn("rounded-xl border-2 p-5", cfg.bg, cfg.border)}>
        <div className="flex items-start gap-3">
          <UrgencyIcon className={cn("size-6 shrink-0 mt-0.5", cfg.text)} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className={cn("text-base font-bold", cfg.text)}>{cfg.label}</span>
              <Badge tone={cfg.badge}>{result.escalation_path}</Badge>
            </div>
            {result.immediate_action && (
              <p className={cn("mt-1.5 text-sm font-medium", cfg.text)}>{result.immediate_action}</p>
            )}
          </div>
        </div>

        {(result.urgency_level === "critical" || result.urgency_level === "urgent") && (
          <a
            href="tel:911"
            className="mt-4 flex items-center justify-center gap-2 w-full py-2.5 rounded-lg bg-danger-600 text-white text-sm font-semibold hover:bg-danger-700 transition-colors"
          >
            <Phone className="size-4" />
            Call Emergency Services (911)
          </a>
        )}
      </div>

      {/* Severity bar */}
      <Card>
        <CardContent className="pt-4 space-y-4">
          <SeverityBar score={result.severity_score} />

          {result.reasoning && (
            <div>
              <p className="text-xs font-medium text-ink-muted mb-1">Assessment reasoning</p>
              <p className="text-sm text-ink leading-relaxed">{result.reasoning}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Warning signs */}
      {result.warning_signs.length > 0 && (
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-danger-700 mb-2">Warning signs identified</p>
            <ul className="space-y-1">
              {result.warning_signs.map((sign, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink">
                  <AlertTriangle className="size-3.5 shrink-0 mt-0.5 text-danger-500" />
                  {sign}
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Next steps */}
      {result.next_steps.length > 0 && (
        <Card>
          <CardContent className="pt-4">
            <p className="text-xs font-medium text-ink-muted mb-2">Recommended next steps</p>
            <ol className="space-y-1.5">
              {result.next_steps.map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-ink">
                  <span className="size-5 shrink-0 rounded-full bg-brand-100 text-brand-700 text-xs font-semibold flex items-center justify-center mt-0.5">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
            </ol>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      {result.disclaimer && (
        <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-md bg-warning-50 border border-warning-100 text-xs text-warning-700">
          <ShieldAlert className="size-4 mt-0.5 shrink-0" />
          <span>{result.disclaimer}</span>
        </div>
      )}

      <Button variant="secondary" onClick={onReset} className="w-full">
        <RotateCcw className="size-4" />
        Start new assessment
      </Button>
    </div>
  );
}

const EXAMPLES = [
  "I have a severe headache and blurred vision for the past hour",
  "My chest feels tight and I'm slightly short of breath",
  "I have a mild sore throat and a low-grade fever (37.8°C)",
  "I cut my finger, it's bleeding but not heavily",
];

export default function TriagePage() {
  const [symptoms, setSymptoms] = useState("");
  const { result, isLoading, error, assess, reset } = useTriage();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (symptoms.trim().length >= 5) assess(symptoms.trim());
  }

  function handleReset() {
    reset();
    setSymptoms("");
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <PageHeader
        title="Symptom Checker"
        description="Describe your symptoms and get an AI urgency assessment. For emergencies, call 911 immediately."
      />

      {result ? (
        <TriageResult result={result} onReset={handleReset} />
      ) : (
        <div className="space-y-5">
          <Card>
            <CardContent className="pt-5">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1.5">
                  <label className="label block" htmlFor="symptoms">
                    Describe your symptoms
                  </label>
                  <textarea
                    id="symptoms"
                    value={symptoms}
                    onChange={(e) => setSymptoms(e.target.value)}
                    placeholder="e.g. I have a sharp chest pain on the left side that started 30 minutes ago, along with shortness of breath and nausea…"
                    rows={5}
                    className={cn(
                      "w-full px-3 py-2.5 rounded-lg bg-bg-elevated border border-border",
                      "text-sm text-ink placeholder:text-ink-subtle resize-y",
                      "outline-none transition-shadow",
                      "focus:border-brand-500 focus:shadow-focus",
                    )}
                  />
                  <p className="text-xs text-ink-subtle">
                    Include when symptoms started, severity, and any relevant medical history.
                  </p>
                </div>

                {error && <p className="text-sm text-danger-600">{error}</p>}

                <Button
                  type="submit"
                  disabled={symptoms.trim().length < 5 || isLoading}
                  loading={isLoading}
                  className="w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Assessing…
                    </>
                  ) : (
                    <>
                      Assess symptoms
                      <ArrowRight className="size-4" />
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Example prompts */}
          <div>
            <p className="text-xs text-ink-muted mb-2 font-medium">Try an example:</p>
            <div className="grid gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setSymptoms(ex)}
                  className="text-left text-sm px-3 py-2.5 rounded-lg border border-border bg-bg-elevated hover:border-brand-400 hover:bg-brand-50 transition-colors flex items-start gap-2"
                >
                  <ArrowRight className="size-3.5 shrink-0 mt-0.5 text-brand-500" />
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-start gap-2.5 px-3 py-2.5 rounded-md bg-warning-50 border border-warning-100 text-xs text-warning-700">
            <ShieldAlert className="size-4 mt-0.5 shrink-0" />
            <span>
              This tool is not a substitute for professional medical advice. If you believe you are
              experiencing a medical emergency, call 911 immediately.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
