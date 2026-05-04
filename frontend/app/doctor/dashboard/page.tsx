"use client";

import Link from "next/link";
import { Users, AlertCircle, Activity, ChevronRight, CalendarCheck } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Loader } from "@/components/ui/Loader";
import { useDoctorPatients, useDoctorAppointments, useUnreadMessageCount } from "@/hooks/useDoctor";
import type { VitalStatus } from "@/lib/api";

function statusTone(s: VitalStatus): "danger" | "warning" | "brand" | "success" | "neutral" {
  if (s === "CRITICAL") return "danger";
  if (s === "HIGH") return "warning";
  if (s === "MODERATE") return "brand";
  if (s === "NORMAL") return "success";
  return "neutral";
}

export default function DoctorDashboardPage() {
  const { data, isLoading } = useDoctorPatients(100, 0);
  const { data: apptData } = useDoctorAppointments();
  const { data: msgData } = useUnreadMessageCount();

  const items = data?.items ?? [];
  const total = data?.total ?? 0;

  const criticalCount = items.filter(
    (p) => p.latest_vital_status === "CRITICAL" || p.latest_vital_status === "HIGH",
  ).length;

  const recentVitals = items.filter((p) => p.latest_vital_timestamp).length;
  const pendingAppts = apptData?.items.filter((a) => a.status === "pending") ?? [];
  const unreadMsgs = msgData?.total_unread ?? 0;

  const recentPatients = [...items]
    .filter((p) => p.latest_vital_timestamp)
    .sort(
      (a, b) =>
        new Date(b.latest_vital_timestamp!).getTime() -
        new Date(a.latest_vital_timestamp!).getTime(),
    )
    .slice(0, 5);

  return (
    <div className="container py-8 max-w-7xl">
      <PageHeader
        title="Doctor Dashboard"
        description="Overview of your patients and their vitals."
      />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-sm font-medium">Total Patients</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "—" : total}</div>
            <p className="text-xs text-muted-foreground mt-1">In the system</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-sm font-medium">Critical Alerts</CardTitle>
            <AlertCircle className="h-4 w-4 text-danger-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "—" : criticalCount}</div>
            <p className="text-xs text-muted-foreground mt-1">High or critical status</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-sm font-medium">Patients with Vitals</CardTitle>
            <Activity className="h-4 w-4 text-brand-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{isLoading ? "—" : recentVitals}</div>
            <p className="text-xs text-muted-foreground mt-1">At least one recorded reading</p>
          </CardContent>
        </Card>

        <Link href="/doctor/appointments">
          <Card className="h-full hover:border-warning-300 transition-colors cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
              <CardTitle className="text-sm font-medium">Pending Appointments</CardTitle>
              <CalendarCheck className="h-4 w-4 text-warning-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-warning-600">{pendingAppts.length}</div>
              <p className="text-xs text-muted-foreground mt-1">Awaiting confirmation</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-8">
                <Loader label="Loading patients…" />
              </div>
            ) : recentPatients.length === 0 ? (
              <p className="text-sm text-ink-subtle italic py-4">
                No recent vitals recorded yet.
              </p>
            ) : (
              <div className="divide-y divide-border">
                {recentPatients.map((p) => (
                  <Link
                    key={p.id}
                    href={`/doctor/patients/${p.id}`}
                    className="flex items-center justify-between py-3 -mx-6 px-6 hover:bg-bg-subtle transition-colors group"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-ink group-hover:text-brand-700 transition-colors">
                        {p.full_name || "Unknown"}
                      </p>
                      <p className="text-xs text-ink-subtle mt-0.5">
                        Last vitals{" "}
                        {new Date(p.latest_vital_timestamp!).toLocaleString(undefined, {
                          month: "short",
                          day: "numeric",
                          hour: "numeric",
                          minute: "2-digit",
                        })}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge tone={statusTone(p.latest_vital_status)}>
                        {p.latest_vital_status}
                      </Badge>
                      <ChevronRight className="size-4 text-ink-muted group-hover:text-brand-700 transition-colors" />
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <div className="flex flex-col gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Link href="/doctor/patients">
                <Button fullWidth>View All Patients</Button>
              </Link>
              <Link href="/doctor/messages">
                <Button fullWidth variant="secondary">
                  Messages
                  {unreadMsgs > 0 && (
                    <span className="ml-auto min-w-[18px] h-[18px] px-1 rounded-full bg-brand-500 text-white text-[10px] font-bold flex items-center justify-center">
                      {unreadMsgs > 9 ? "9+" : unreadMsgs}
                    </span>
                  )}
                </Button>
              </Link>
              <Link href="/doctor/appointments">
                <Button fullWidth variant="secondary">
                  Appointment Requests
                  {pendingAppts.length > 0 && (
                    <span className="ml-auto min-w-[18px] h-[18px] px-1 rounded-full bg-warning-500 text-white text-[10px] font-bold flex items-center justify-center">
                      {pendingAppts.length > 9 ? "9+" : pendingAppts.length}
                    </span>
                  )}
                </Button>
              </Link>
            </CardContent>
          </Card>

          {pendingAppts.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Recent Requests</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border">
                  {pendingAppts.slice(0, 3).map((a) => (
                    <Link
                      key={a.id}
                      href="/doctor/appointments"
                      className="flex items-start gap-2.5 py-3 px-6 hover:bg-bg-subtle transition-colors group"
                    >
                      <CalendarCheck className="size-4 text-warning-500 shrink-0 mt-0.5" />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-ink truncate group-hover:text-brand-700">
                          {a.patient_name ?? "Patient"}
                        </p>
                        <p className="text-xs text-ink-muted truncate">{a.reason}</p>
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
