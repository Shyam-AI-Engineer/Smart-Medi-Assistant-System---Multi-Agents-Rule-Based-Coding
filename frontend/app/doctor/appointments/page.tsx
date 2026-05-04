"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CalendarCheck, Calendar, Clock, User, Loader2, X,
  CheckCircle, XCircle, RotateCcw, ChevronDown, FileText, Download,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Loader } from "@/components/ui/Loader";
import { useDoctorAppointments } from "@/hooks/useDoctor";
import { endpoints, type AppointmentItem, type AppointmentStatus } from "@/lib/api";
import { cn } from "@/lib/cn";

// ── Types & helpers ───────────────────────────────────────────────────────────

type FilterTab = "all" | AppointmentStatus;

const TABS: { key: FilterTab; label: string }[] = [
  { key: "all",       label: "All" },
  { key: "pending",   label: "Pending" },
  { key: "confirmed", label: "Confirmed" },
  { key: "completed", label: "Completed" },
  { key: "cancelled", label: "Cancelled" },
];

const STATUS_TONE: Record<AppointmentStatus, "warning" | "success" | "neutral" | "danger"> = {
  pending:   "warning",
  confirmed: "success",
  completed: "neutral",
  cancelled: "danger",
};

function fmt(iso: string) {
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric", month: "short", year: "numeric",
  });
}

// ── Confirm modal ─────────────────────────────────────────────────────────────

function ConfirmModal({
  appt,
  onClose,
}: {
  appt: AppointmentItem;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [scheduledAt, setScheduledAt] = useState(appt.scheduled_at ?? "");
  const [notes, setNotes] = useState(appt.doctor_notes ?? "");

  const mutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      endpoints.updateAppointment(appt.id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["doctor-appointments"] });
      onClose();
    },
  });

  const confirm = () =>
    mutation.mutate({ status: "confirmed", scheduled_at: scheduledAt, doctor_notes: notes });

  const today = new Date().toISOString().slice(0, 16);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border bg-bg shadow-xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="font-semibold text-ink">Confirm Appointment</h2>
          <button
            onClick={onClose}
            className="size-8 rounded-md flex items-center justify-center text-ink-muted hover:bg-bg-subtle"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="px-3 py-2.5 rounded-lg bg-bg-subtle border border-border text-sm">
            <p className="font-medium text-ink">{appt.patient_name ?? "Patient"}</p>
            <p className="text-ink-muted mt-0.5">{appt.reason}</p>
            {appt.preferred_date && (
              <p className="text-xs text-ink-subtle mt-1">
                Preferred: {appt.preferred_date}
                {appt.preferred_time_slot && appt.preferred_time_slot !== "any"
                  ? ` · ${appt.preferred_time_slot}`
                  : ""}
              </p>
            )}
            {appt.attachment_path && (
              <div className="mt-2 pt-2 border-t border-border/50 flex items-center gap-2">
                <FileText className="size-3 text-brand-600 shrink-0" />
                <span className="text-xs text-ink truncate flex-1">{appt.attachment_path}</span>
                <a
                  href={`/api/appointments/files/${appt.id}/${appt.attachment_path}`}
                  download
                  className="p-1 rounded text-ink-muted hover:text-brand-600 hover:bg-brand-50 transition-colors shrink-0"
                  title="Download attachment"
                >
                  <Download className="size-3" />
                </a>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">
              Scheduled date & time <span className="text-danger-500">*</span>
            </label>
            <input
              type="datetime-local"
              min={today}
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">
              Note to patient <span className="text-ink-subtle font-normal">(optional)</span>
            </label>
            <textarea
              rows={3}
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-sm text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
              placeholder="e.g. Please bring your medication list and previous test reports."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          {mutation.isError && (
            <p className="text-xs text-danger-600">Failed to update — please try again.</p>
          )}
        </div>

        <div className="flex justify-end gap-2 px-6 py-4 border-t border-border">
          <Button variant="secondary" size="md" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={confirm}
            disabled={!scheduledAt || mutation.isPending}
          >
            {mutation.isPending ? (
              <><Loader2 className="size-4 animate-spin" /> Saving…</>
            ) : (
              <><CheckCircle className="size-4" /> Confirm appointment</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

// ── Appointment row ───────────────────────────────────────────────────────────

function AppointmentRow({
  appt,
  onConfirm,
  onCancel,
  onComplete,
  actionPending,
}: {
  appt: AppointmentItem;
  onConfirm: (a: AppointmentItem) => void;
  onCancel: (id: string) => void;
  onComplete: (id: string) => void;
  actionPending: boolean;
}) {
  return (
    <div className="rounded-xl border border-border bg-bg-elevated p-5">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-start gap-3">
          <div className="size-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0 mt-0.5">
            <User className="size-4" />
          </div>
          <div>
            <p className="font-semibold text-ink text-sm">{appt.patient_name ?? "Patient"}</p>
            <p className="text-sm text-ink-muted mt-0.5 leading-snug">{appt.reason}</p>
            <div className="flex flex-wrap gap-3 mt-2 text-xs text-ink-subtle">
              <span className="flex items-center gap-1">
                <Calendar className="size-3" />
                Requested {fmt(appt.created_at)}
              </span>
              {appt.preferred_date && (
                <span className="flex items-center gap-1">
                  <Clock className="size-3" />
                  Preferred {appt.preferred_date}
                  {appt.preferred_time_slot && appt.preferred_time_slot !== "any"
                    ? ` · ${appt.preferred_time_slot}`
                    : ""}
                </span>
              )}
              {appt.ai_suggested && (
                <span className="flex items-center gap-1 text-brand-600">
                  <CalendarCheck className="size-3" />
                  AI suggested
                </span>
              )}
            </div>
          </div>
        </div>

        <Badge tone={STATUS_TONE[appt.status]}>
          {appt.status.charAt(0).toUpperCase() + appt.status.slice(1)}
        </Badge>
      </div>

      {appt.scheduled_at && (
        <div className="mt-3 px-3 py-2 rounded-lg bg-success-50 border border-success-100 text-xs text-success-700">
          <span className="font-semibold">Scheduled:</span>{" "}
          {new Date(appt.scheduled_at).toLocaleString("en-IN", {
            weekday: "short", day: "numeric", month: "short",
            hour: "numeric", minute: "2-digit",
          })}
        </div>
      )}

      {appt.doctor_notes && (
        <div className="mt-2 px-3 py-2 rounded-lg bg-bg-subtle border border-border text-xs text-ink">
          <span className="font-semibold text-ink-muted">Your note:</span> {appt.doctor_notes}
        </div>
      )}

      {appt.attachment_path && (
        <div className="mt-2 px-3 py-2 rounded-lg border border-border bg-bg-subtle flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <FileText className="size-4 text-brand-600 shrink-0" />
            <span className="text-xs text-ink truncate">{appt.attachment_path}</span>
          </div>
          <a
            href={`/api/appointments/files/${appt.id}/${appt.attachment_path}`}
            download
            className="ml-2 p-1.5 rounded text-ink-muted hover:text-brand-600 hover:bg-brand-50 transition-colors shrink-0"
            title="Download attachment"
          >
            <Download className="size-3.5" />
          </a>
        </div>
      )}

      {(appt.status === "pending" || appt.status === "confirmed") && (
        <div className="mt-3 flex flex-wrap gap-2 justify-end">
          {appt.status === "pending" && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => onConfirm(appt)}
              disabled={actionPending}
            >
              <CheckCircle className="size-3.5" />
              Confirm
            </Button>
          )}
          {appt.status === "confirmed" && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onComplete(appt.id)}
              disabled={actionPending}
            >
              <RotateCcw className="size-3.5" />
              Mark completed
            </Button>
          )}
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onCancel(appt.id)}
            disabled={actionPending}
            className="text-danger-600 hover:text-danger-700 hover:bg-danger-50 border-danger-200"
          >
            <XCircle className="size-3.5" />
            Cancel
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function DoctorAppointmentsPage() {
  const [tab, setTab] = useState<FilterTab>("all");
  const [confirmAppt, setConfirmAppt] = useState<AppointmentItem | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useDoctorAppointments();

  const allItems = data?.items ?? [];

  const pendingCount = allItems.filter((a) => a.status === "pending").length;

  const filtered =
    tab === "all" ? allItems : allItems.filter((a) => a.status === tab);

  const actionMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      endpoints.updateAppointment(id, payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["doctor-appointments"] }),
  });

  const cancel  = (id: string) => actionMutation.mutate({ id, payload: { status: "cancelled" } });
  const complete = (id: string) => actionMutation.mutate({ id, payload: { status: "completed" } });

  return (
    <div className="container max-w-4xl py-8 space-y-6">
      <PageHeader
        title="Appointment Requests"
        description="Review, confirm, and schedule patient appointments."
      />

      {/* Filter tabs */}
      <div className="flex gap-1 p-1 rounded-lg bg-bg-subtle border border-border w-fit">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "px-3 py-1.5 rounded-md text-sm font-medium transition-colors relative",
              tab === t.key
                ? "bg-bg shadow-sm text-ink"
                : "text-ink-muted hover:text-ink",
            )}
          >
            {t.label}
            {t.key === "pending" && pendingCount > 0 && (
              <span className="ml-1.5 min-w-[18px] h-[18px] px-1 rounded-full bg-warning-500 text-white text-[10px] font-bold inline-flex items-center justify-center">
                {pendingCount > 9 ? "9+" : pendingCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="py-16">
          <Loader label="Loading appointments…" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <CalendarCheck className="size-8 mx-auto text-ink-subtle mb-3" />
          <p className="text-sm font-medium text-ink">
            No {tab === "all" ? "" : tab} appointments
          </p>
          <p className="text-xs text-ink-muted mt-1">
            Patients can request appointments from the patient portal.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((a) => (
            <AppointmentRow
              key={a.id}
              appt={a}
              onConfirm={setConfirmAppt}
              onCancel={cancel}
              onComplete={complete}
              actionPending={actionMutation.isPending}
            />
          ))}
        </div>
      )}

      {confirmAppt && (
        <ConfirmModal appt={confirmAppt} onClose={() => setConfirmAppt(null)} />
      )}
    </div>
  );
}
