"use client";

import { useState, useRef, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Calendar, Clock, Plus, X, CheckCircle, AlertCircle, Loader2, CalendarCheck, Mic, MicOff, Paperclip, FileText } from "lucide-react";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { endpoints, type AppointmentItem, type AppointmentStatus } from "@/lib/api";
import { cn } from "@/lib/cn";

const TIME_SLOTS = ["morning", "afternoon", "evening", "any"] as const;

const STATUS_CONFIG: Record<AppointmentStatus, { label: string; className: string }> = {
  pending:   { label: "Pending",   className: "bg-warning-50 text-warning-700 border-warning-200" },
  confirmed: { label: "Confirmed", className: "bg-success-50 text-success-700 border-success-200" },
  cancelled: { label: "Cancelled", className: "bg-danger-50 text-danger-700 border-danger-200" },
  completed: { label: "Completed", className: "bg-bg-subtle text-ink-muted border-border" },
};

function StatusBadge({ status }: { status: AppointmentStatus }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.pending;
  return (
    <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium border", cfg.className)}>
      {cfg.label}
    </span>
  );
}

function AppointmentCard({
  appt,
  onCancel,
  cancelling,
}: {
  appt: AppointmentItem;
  onCancel: (id: string) => void;
  cancelling: boolean;
}) {
  const date = new Date(appt.created_at);
  return (
    <div className="rounded-xl border border-border bg-bg-elevated p-5 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="size-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">
            <CalendarCheck className="size-4" />
          </div>
          <div>
            <p className="font-semibold text-ink text-sm leading-tight">
              {appt.reason}
            </p>
            <p className="text-xs text-ink-muted mt-0.5">
              Requested {date.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
            </p>
          </div>
        </div>
        <StatusBadge status={appt.status} />
      </div>

      <div className="flex flex-wrap gap-4 text-xs text-ink-muted">
        {appt.preferred_date && (
          <span className="flex items-center gap-1">
            <Calendar className="size-3.5" />
            Preferred: {appt.preferred_date}
          </span>
        )}
        {appt.preferred_time_slot && appt.preferred_time_slot !== "any" && (
          <span className="flex items-center gap-1">
            <Clock className="size-3.5" />
            {appt.preferred_time_slot.charAt(0).toUpperCase() + appt.preferred_time_slot.slice(1)}
          </span>
        )}
        {appt.ai_suggested && (
          <span className="flex items-center gap-1 text-brand-600">
            <CheckCircle className="size-3.5" />
            AI suggested
          </span>
        )}
      </div>

      {appt.scheduled_at && (
        <div className="px-3 py-2 rounded-lg bg-success-50 border border-success-100 text-xs text-success-700">
          <span className="font-semibold">Scheduled:</span> {appt.scheduled_at}
        </div>
      )}

      {appt.doctor_notes && (
        <div className="px-3 py-2 rounded-lg bg-bg-subtle border border-border text-xs text-ink">
          <span className="font-semibold text-ink-muted">Doctor&rsquo;s note:</span> {appt.doctor_notes}
        </div>
      )}

      {appt.status === "pending" && (
        <div className="flex justify-end">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onCancel(appt.id)}
            disabled={cancelling}
            className="text-danger-600 hover:text-danger-700 hover:bg-danger-50 border-danger-200"
          >
            <X className="size-3.5" />
            Cancel request
          </Button>
        </div>
      )}
    </div>
  );
}

function RequestForm({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [reason, setReason] = useState("");
  const [preferredDate, setPreferredDate] = useState("");
  const [timeSlot, setTimeSlot] = useState<string>("any");
  const [attachedFile, setAttachedFile] = useState<File | null>(null);
  const [attachError, setAttachError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { state: recorderState, transcript, error: voiceError, startRecording, stopRecording, reset: resetVoice } = useVoiceRecorder();
  const isRecording = recorderState === "recording";

  useEffect(() => {
    if (!transcript) return;
    setReason((prev) => (prev ? prev + " " + transcript : transcript));
    resetVoice();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transcript]);

  const mutation = useMutation({
    mutationFn: () =>
      endpoints.requestAppointment({
        reason,
        preferred_date: preferredDate || null,
        preferred_time_slot: timeSlot,
        ai_suggested: false,
        attachment: attachedFile ?? undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      onSuccess();
    },
  });

  const today = new Date().toISOString().split("T")[0];

  const ATTACH_ALLOWED = [".pdf", ".jpg", ".jpeg", ".png", ".docx"];
  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    e.target.value = "";
    if (!file) return;
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf("."));
    if (!ATTACH_ALLOWED.includes(ext)) {
      setAttachError(`Unsupported file type. Allowed: ${ATTACH_ALLOWED.join(", ")}`);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setAttachError("File too large (max 10 MB)");
      return;
    }
    setAttachError(null);
    setAttachedFile(file);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border bg-bg shadow-xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="font-semibold text-ink">Request Appointment</h2>
          <button
            onClick={onClose}
            className="size-8 rounded-md flex items-center justify-center text-ink-muted hover:bg-bg-subtle transition-colors"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">
              Reason for appointment <span className="text-danger-500">*</span>
            </label>
            <div className="relative flex items-start gap-2">
              <textarea
                className="flex-1 px-3 py-2.5 rounded-lg border border-border bg-bg text-sm text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
                rows={3}
                placeholder="e.g. Follow-up on blood pressure readings, general check-up…"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              <button
                type="button"
                onClick={() => (isRecording ? stopRecording() : startRecording())}
                aria-label={isRecording ? "Stop recording" : "Dictate reason"}
                title={isRecording ? "Stop recording" : "Use voice to fill reason"}
                className={cn(
                  "mt-0.5 size-8 shrink-0 rounded-lg flex items-center justify-center transition-colors",
                  isRecording
                    ? "bg-red-500 text-white hover:bg-red-600 animate-pulse"
                    : "bg-bg-subtle text-ink-muted hover:bg-bg-hover hover:text-ink",
                )}
              >
                {isRecording ? <MicOff className="size-4" /> : <Mic className="size-4" />}
              </button>
            </div>
            {isRecording && (
              <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
                <span className="inline-block size-2 rounded-full bg-red-500 animate-pulse" />
                Listening… click the mic again to stop
              </p>
            )}
            {voiceError && (
              <p className="mt-1 text-xs text-danger-600">{voiceError}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">
              Preferred date <span className="text-ink-subtle font-normal">(optional)</span>
            </label>
            <input
              type="date"
              min={today}
              className="w-full px-3 py-2.5 rounded-lg border border-border bg-bg text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              value={preferredDate}
              onChange={(e) => setPreferredDate(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">Preferred time</label>
            <div className="flex gap-2 flex-wrap">
              {TIME_SLOTS.map((slot) => (
                <button
                  key={slot}
                  type="button"
                  onClick={() => setTimeSlot(slot)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors",
                    timeSlot === slot
                      ? "bg-brand-500 text-white border-brand-500"
                      : "bg-bg border-border text-ink-muted hover:border-border-strong",
                  )}
                >
                  {slot.charAt(0).toUpperCase() + slot.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-ink mb-1.5">
              Attach a document <span className="text-ink-subtle font-normal">(optional — lab results, reports)</span>
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.docx"
              className="hidden"
              onChange={handleFileChange}
            />
            {attachedFile ? (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-bg-subtle">
                <FileText className="size-4 text-brand-600 shrink-0" />
                <span className="text-sm text-ink truncate flex-1">{attachedFile.name}</span>
                <button
                  type="button"
                  onClick={() => {
                    setAttachedFile(null);
                    setAttachError(null);
                  }}
                  className="size-5 flex items-center justify-center rounded text-ink-muted hover:text-danger-600 hover:bg-danger-50 transition-colors"
                  aria-label="Remove attachment"
                >
                  <X className="size-3.5" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-border text-ink-muted text-sm hover:border-brand-400 hover:text-brand-600 transition-colors w-full"
              >
                <Paperclip className="size-4" />
                Attach file (PDF, JPG, PNG, DOCX — max 10 MB)
              </button>
            )}
            {attachError && (
              <p className="mt-1 text-xs text-danger-600 flex items-center gap-1">
                <AlertCircle className="size-3.5" /> {attachError}
              </p>
            )}
          </div>

          {mutation.isError && (
            <p className="text-xs text-danger-600 flex items-center gap-1">
              <AlertCircle className="size-3.5" /> Failed to submit — please try again.
            </p>
          )}
        </div>

        <div className="flex justify-end gap-2 px-6 py-4 border-t border-border">
          <Button variant="secondary" size="md" onClick={onClose} disabled={mutation.isPending}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={() => mutation.mutate()}
            disabled={!reason.trim() || mutation.isPending}
          >
            {mutation.isPending ? (
              <><Loader2 className="size-4 animate-spin" /> Submitting…</>
            ) : (
              <><Plus className="size-4" /> Request appointment</>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function AppointmentsPage() {
  const [showForm, setShowForm] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["appointments"],
    queryFn: endpoints.listAppointments,
  });

  const cancelMutation = useMutation({
    mutationFn: (id: string) => endpoints.cancelAppointment(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["appointments"] }),
  });

  const appts = data?.items ?? [];
  const upcoming = appts.filter((a) => a.status === "pending" || a.status === "confirmed");
  const past = appts.filter((a) => a.status === "cancelled" || a.status === "completed");

  return (
    <div className="container max-w-3xl py-8 space-y-6">
      <PageHeader
        title="Appointments"
        description="Request and track your appointment schedule."
        actions={
          <Button variant="primary" size="md" onClick={() => setShowForm(true)}>
            <Plus className="size-4" /> Request appointment
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="size-6 animate-spin text-ink-muted" />
        </div>
      ) : appts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <Calendar className="size-8 mx-auto text-ink-subtle mb-3" />
          <p className="text-sm font-medium text-ink">No appointments yet</p>
          <p className="text-xs text-ink-muted mt-1">
            Request one below, or ask the AI Chat for a recommendation.
          </p>
          <Button
            variant="secondary"
            size="md"
            className="mt-4"
            onClick={() => setShowForm(true)}
          >
            <Plus className="size-4" /> Request appointment
          </Button>
        </div>
      ) : (
        <>
          {upcoming.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-ink-muted uppercase tracking-wide">
                Upcoming
              </h2>
              {upcoming.map((a) => (
                <AppointmentCard
                  key={a.id}
                  appt={a}
                  onCancel={(id) => cancelMutation.mutate(id)}
                  cancelling={cancelMutation.isPending}
                />
              ))}
            </section>
          )}

          {past.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-sm font-semibold text-ink-muted uppercase tracking-wide">
                Past
              </h2>
              {past.map((a) => (
                <AppointmentCard
                  key={a.id}
                  appt={a}
                  onCancel={(id) => cancelMutation.mutate(id)}
                  cancelling={cancelMutation.isPending}
                />
              ))}
            </section>
          )}
        </>
      )}

      {showForm && (
        <RequestForm
          onClose={() => setShowForm(false)}
          onSuccess={() => setShowForm(false)}
        />
      )}
    </div>
  );
}
