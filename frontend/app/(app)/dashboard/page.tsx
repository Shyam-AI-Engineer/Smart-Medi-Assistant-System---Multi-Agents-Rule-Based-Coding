"use client";

import Link from "next/link";
import { useMemo } from "react";
import { Heart, Activity, Wind, Thermometer, Plus, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loader } from "@/components/ui/Loader";
import { EmptyState } from "@/components/ui/EmptyState";
import { MetricCard, type Trend } from "@/components/dashboard/MetricCard";
import { VitalsChart, type ChartPoint } from "@/components/dashboard/VitalsChart";
import { useMyPatientProfile, useVitalsHistory } from "@/hooks/useVitals";
import { formatDateTime, relativeTime } from "@/lib/format";
import type { VitalRecord } from "@/lib/api";

type Metric = "heart_rate" | "blood_pressure_systolic" | "oxygen_saturation" | "temperature";

function buildSeries(records: VitalRecord[], metric: Metric): ChartPoint[] {
  // newest first → reverse for chart
  return [...records]
    .reverse()
    .map((r) => ({
      time: new Date(r.created_at).toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      value: (r[metric] ?? null) as number | null,
    }));
}

function computeTrend(records: VitalRecord[], metric: Metric, lowerIsBad = false): Trend {
  const values = records
    .map((r) => r[metric])
    .filter((v): v is number => typeof v === "number");
  if (values.length < 2) return "none" as const;
  const latest = values[0];
  const prev = values.slice(1, 5);
  const avg = prev.reduce((a, b) => a + b, 0) / prev.length;
  const change = (latest - avg) / Math.abs(avg || 1);
  const threshold = 0.05;
  if (Math.abs(change) < threshold) return "stable" as const;
  const rising = change > 0;
  if (lowerIsBad) return rising ? "improving" : "worsening";
  return rising ? "worsening" : "improving";
}

export default function DashboardPage() {
  const { data: profile } = useMyPatientProfile();
  const { data, isLoading } = useVitalsHistory(profile?.id, 30);

  const records = data?.items ?? [];
  const latest = records[0];

  const series = useMemo(
    () => ({
      hr: buildSeries(records, "heart_rate"),
      bp: buildSeries(records, "blood_pressure_systolic"),
      spo2: buildSeries(records, "oxygen_saturation"),
      temp: buildSeries(records, "temperature"),
    }),
    [records],
  );

  const trends = useMemo(
    () => ({
      hr: computeTrend(records, "heart_rate"),
      bp: computeTrend(records, "blood_pressure_systolic"),
      spo2: computeTrend(records, "oxygen_saturation", true),
      temp: computeTrend(records, "temperature"),
    }),
    [records],
  );

  return (
    <div className="container py-8 max-w-7xl">
      <PageHeader
        title="Dashboard"
        description="Overview of your most recent vitals and trends."
        actions={
          <>
            <Link href="/chat">
              <Button variant="secondary" size="md">
                <Sparkles className="size-4" /> Ask AI
              </Button>
            </Link>
            <Link href="/vitals">
              <Button size="md">
                <Plus className="size-4" /> Record vitals
              </Button>
            </Link>
          </>
        }
      />

      {isLoading ? (
        <div className="py-24">
          <Loader label="Loading your data…" />
        </div>
      ) : records.length === 0 ? (
        <Card className="mt-8">
          <EmptyState
            icon={<Activity className="size-5" />}
            title="No vitals recorded yet"
            description="Record your first measurement to start seeing trends and AI insights."
            action={
              <Link href="/vitals">
                <Button>
                  <Plus className="size-4" /> Record vitals
                </Button>
              </Link>
            }
          />
        </Card>
      ) : (
        <>
          {/* Last update strip */}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-3">
              <Badge tone="brand" dot>Last reading</Badge>
              <span className="text-ink-muted">
                {formatDateTime(latest?.created_at)} ·{" "}
                <span className="text-ink-subtle">{relativeTime(latest?.created_at)}</span>
              </span>
            </div>
            {latest?.anomaly_detected && (
              <Badge tone="danger" dot>
                Anomaly detected
              </Badge>
            )}
          </div>

          {/* Metric cards */}
          <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <MetricCard
              label="Heart rate"
              value={latest?.heart_rate ?? "—"}
              unit="bpm"
              trend={trends.hr}
              icon={<Heart className="size-4" />}
              hint="Normal 60–100"
            />
            <MetricCard
              label="Blood pressure"
              value={
                latest?.blood_pressure_systolic && latest?.blood_pressure_diastolic
                  ? `${latest.blood_pressure_systolic}/${latest.blood_pressure_diastolic}`
                  : "—"
              }
              unit="mmHg"
              trend={trends.bp}
              icon={<Activity className="size-4" />}
              hint="Normal <120/80"
            />
            <MetricCard
              label="SpO₂"
              value={latest?.oxygen_saturation ?? "—"}
              unit="%"
              trend={trends.spo2}
              icon={<Wind className="size-4" />}
              hint="Normal 95–100"
            />
            <MetricCard
              label="Temperature"
              value={latest?.temperature ?? "—"}
              unit="°C"
              trend={trends.temp}
              icon={<Thermometer className="size-4" />}
              hint="Normal 36.1–37.2"
            />
          </div>

          {/* Charts */}
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
            <VitalsChart
              title="Heart Rate"
              description="Beats per minute"
              data={series.hr}
              unit="bpm"
              color="#EF4444"
              normalRange={{ min: 60, max: 100 }}
            />
            <VitalsChart
              title="Blood Pressure (Systolic)"
              description="Top number, mmHg"
              data={series.bp}
              unit="mmHg"
              color="#1E86EE"
              normalRange={{ min: 90, max: 120 }}
            />
            <VitalsChart
              title="Oxygen Saturation"
              description="SpO₂ %"
              data={series.spo2}
              unit="%"
              color="#10B981"
              normalRange={{ min: 95, max: 100 }}
            />
            <VitalsChart
              title="Temperature"
              description="Body temperature, °C"
              data={series.temp}
              unit="°C"
              color="#F59E0B"
              normalRange={{ min: 36.1, max: 37.2 }}
            />
          </div>

          {/* Recent readings table */}
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Recent readings</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-bg-subtle/60 text-ink-muted">
                    <tr className="text-left">
                      <th className="px-6 py-3 font-medium">Time</th>
                      <th className="px-6 py-3 font-medium">HR</th>
                      <th className="px-6 py-3 font-medium">BP</th>
                      <th className="px-6 py-3 font-medium">SpO₂</th>
                      <th className="px-6 py-3 font-medium">Temp</th>
                      <th className="px-6 py-3 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {records.slice(0, 8).map((r) => (
                      <tr key={r.id} className="hover:bg-bg-subtle/40 transition-colors">
                        <td className="px-6 py-3 text-ink-muted whitespace-nowrap">
                          {formatDateTime(r.created_at)}
                        </td>
                        <td className="px-6 py-3 text-ink">{r.heart_rate ?? "—"}</td>
                        <td className="px-6 py-3 text-ink">
                          {r.blood_pressure_systolic && r.blood_pressure_diastolic
                            ? `${r.blood_pressure_systolic}/${r.blood_pressure_diastolic}`
                            : "—"}
                        </td>
                        <td className="px-6 py-3 text-ink">{r.oxygen_saturation ?? "—"}</td>
                        <td className="px-6 py-3 text-ink">{r.temperature ?? "—"}</td>
                        <td className="px-6 py-3">
                          {r.anomaly_detected ? (
                            <Badge tone="danger" dot>
                              Flagged
                            </Badge>
                          ) : (
                            <Badge tone="success" dot>
                              Normal
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
