"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { ArrowLeft, Calendar } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loader } from "@/components/ui/Loader";
import { EmptyState } from "@/components/ui/EmptyState";
import { VitalsChart, type ChartPoint } from "@/components/dashboard/VitalsChart";
import { usePatientDetail } from "@/hooks/useDoctor";
import { formatDateTime } from "@/lib/format";
import type { VitalRecord } from "@/lib/api";

type Metric = "heart_rate" | "blood_pressure_systolic" | "oxygen_saturation" | "temperature";

function buildSeries(records: VitalRecord[], metric: Metric): ChartPoint[] {
  return [...records]
    .reverse()
    .map((r) => ({
      time: new Date(r.created_at).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      }),
      value: (r[metric] ?? null) as number | null,
    }));
}

function buildVitalsDisplay(vital: VitalRecord) {
  const items = [];
  if (vital.heart_rate !== null && vital.heart_rate !== undefined) {
    items.push({ label: "Heart Rate", value: `${vital.heart_rate} bpm` });
  }
  if (
    vital.blood_pressure_systolic !== null &&
    vital.blood_pressure_systolic !== undefined
  ) {
    items.push({
      label: "Blood Pressure",
      value: `${vital.blood_pressure_systolic}/${vital.blood_pressure_diastolic || "?"} mmHg`,
    });
  }
  if (vital.temperature !== null && vital.temperature !== undefined) {
    items.push({ label: "Temperature", value: `${vital.temperature.toFixed(1)}°C` });
  }
  if (vital.oxygen_saturation !== null && vital.oxygen_saturation !== undefined) {
    items.push({
      label: "O₂ Saturation",
      value: `${vital.oxygen_saturation.toFixed(1)}%`,
    });
  }
  return items;
}

export default function PatientDetailPage() {
  const params = useParams<{ patient_id: string }>();
  const patientId = params?.patient_id as string | undefined;

  const { data, isLoading } = usePatientDetail(patientId, 30, 20);

  if (isLoading) {
    return (
      <div className="py-24">
        <Loader label="Loading patient details…" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="container py-8 max-w-5xl">
        <EmptyState
          title="Patient not found"
          description="This patient could not be found in the system."
        />
      </div>
    );
  }

  const patient = data.patient;
  const vitals = data.vitals ?? [];
  const chatHistory = data.chat_history ?? [];
  const summary = data.summary ?? {};
  const latestVital = vitals[0];

  const series = useMemo(
    () => ({
      hr: buildSeries(vitals, "heart_rate"),
      bp: buildSeries(vitals, "blood_pressure_systolic"),
      spo2: buildSeries(vitals, "oxygen_saturation"),
      temp: buildSeries(vitals, "temperature"),
    }),
    [vitals],
  );

  return (
    <div className="container py-8 max-w-5xl">
      <Link href="/doctor/patients" className="inline-flex items-center gap-2 mb-6">
        <ArrowLeft className="size-4" />
        <span className="text-sm font-medium text-ink-muted hover:text-ink transition-colors">
          Back to Patients
        </span>
      </Link>

      {/* Patient Header */}
      <PageHeader
        title={patient.full_name || "Unknown Patient"}
        description={`ID: ${patient.id} • ${patient.user?.email || "No email"}`}
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-ink-subtle uppercase">
              Latest Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              tone={
                summary.latest_status === "CRITICAL"
                  ? "danger"
                  : summary.latest_status === "HIGH"
                    ? "warning"
                    : summary.latest_status === "MODERATE"
                      ? "brand"
                      : summary.latest_status === "NORMAL"
                        ? "success"
                        : "neutral"
              }
            >
              {summary.latest_status || "UNKNOWN"}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-ink-subtle uppercase">
              Risk Level
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              tone={
                summary.risk_level === "CRITICAL"
                  ? "danger"
                  : summary.risk_level === "HIGH"
                    ? "warning"
                    : summary.risk_level === "MODERATE"
                      ? "brand"
                      : summary.risk_level === "LOW"
                        ? "success"
                        : "neutral"
              }
            >
              {summary.risk_level || "UNKNOWN"}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-ink-subtle uppercase">
              Messages
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold text-ink">{summary.total_messages || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-ink-subtle uppercase">
              Last Reading
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium text-ink">
              {summary.latest_vital_at
                ? new Date(summary.latest_vital_at).toLocaleDateString()
                : "No vitals"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Patient Medical Info */}
        <Card>
          <CardHeader>
            <CardTitle>Medical Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {patient.date_of_birth && (
              <div>
                <p className="text-xs text-ink-subtle uppercase font-medium">Date of Birth</p>
                <p className="text-sm text-ink">
                  {new Date(patient.date_of_birth).toLocaleDateString()}
                </p>
              </div>
            )}
            {patient.allergies && (
              <div>
                <p className="text-xs text-ink-subtle uppercase font-medium">Allergies</p>
                <p className="text-sm text-ink">{patient.allergies}</p>
              </div>
            )}
            {patient.current_medications && (
              <div>
                <p className="text-xs text-ink-subtle uppercase font-medium">Medications</p>
                <p className="text-sm text-ink">{patient.current_medications}</p>
              </div>
            )}
            {patient.medical_history && (
              <div>
                <p className="text-xs text-ink-subtle uppercase font-medium">Medical History</p>
                <p className="text-sm text-ink">{patient.medical_history}</p>
              </div>
            )}
            {patient.emergency_contact && (
              <div>
                <p className="text-xs text-ink-subtle uppercase font-medium">
                  Emergency Contact
                </p>
                <p className="text-sm text-ink">{patient.emergency_contact}</p>
              </div>
            )}
            {!patient.allergies &&
              !patient.current_medications &&
              !patient.medical_history &&
              !patient.emergency_contact &&
              !patient.date_of_birth && (
                <p className="text-sm text-ink-subtle italic">No medical information recorded</p>
              )}
          </CardContent>
        </Card>

        {/* Latest Vitals */}
        {latestVital ? (
          <Card>
            <CardHeader>
              <CardTitle>Latest Vital Reading</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-xs text-ink-subtle">
                <Calendar className="inline size-3 mr-1" />
                {formatDateTime(latestVital.created_at)}
              </p>
              <div className="grid grid-cols-2 gap-3">
                {buildVitalsDisplay(latestVital).map((item) => (
                  <div key={item.label}>
                    <p className="text-xs text-ink-subtle uppercase font-medium">{item.label}</p>
                    <p className="text-sm font-semibold text-ink">{item.value}</p>
                  </div>
                ))}
              </div>
              {latestVital.notes && (
                <div className="text-sm text-ink bg-bg-subtle rounded p-2">{latestVital.notes}</div>
              )}
            </CardContent>
          </Card>
        ) : (
          <EmptyState title="No vitals recorded" description="Patient has not recorded any vital signs yet." />
        )}
      </div>

      {/* Vitals Trend Charts */}
      {vitals.length > 1 && (
        <div className="mt-6">
          <h2 className="text-base font-semibold text-ink mb-4">Vitals Trends</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
        </div>
      )}

      {/* Vitals History */}
      {vitals.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Vitals History (Last {vitals.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 divide-y divide-border">
              {vitals.map((vital) => (
                <div key={vital.id} className="pt-3 first:pt-0">
                  <p className="text-xs text-ink-subtle mb-2">
                    {formatDateTime(vital.created_at)}
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {buildVitalsDisplay(vital).map((item) => (
                      <div key={item.label}>
                        <p className="text-xs text-ink-subtle">{item.label}</p>
                        <p className="text-sm font-medium text-ink">{item.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chat History */}
      {chatHistory.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle>Recent AI Chat History (Last {chatHistory.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 divide-y divide-border">
              {chatHistory.map((chat) => (
                <div key={chat.id} className="pt-4 first:pt-0">
                  <div className="flex items-start justify-between mb-2">
                    <p className="text-xs text-ink-subtle">
                      {formatDateTime(chat.created_at)} • Agent: {chat.agent_used}
                    </p>
                    <Badge tone="brand" className="text-xs">
                      {(chat.confidence_score * 100).toFixed(0)}% confidence
                    </Badge>
                  </div>
                  <div className="space-y-2">
                    <div className="bg-bg-subtle rounded p-3">
                      <p className="text-xs text-ink-subtle font-medium mb-1">Patient asked:</p>
                      <p className="text-sm text-ink">{chat.user_message}</p>
                    </div>
                    <div className="bg-brand-50 rounded p-3">
                      <p className="text-xs text-brand-700 font-medium mb-1">AI responded:</p>
                      <p className="text-sm text-ink line-clamp-3">{chat.ai_response}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
