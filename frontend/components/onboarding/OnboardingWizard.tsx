"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  User, Activity, MessageSquare, Bell,
  ChevronRight, Loader2, CheckCircle2, Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import { endpoints, getApiErrorMessage, type PatientProfile } from "@/lib/api";

// ── Step progress dots ────────────────────────────────────────────────────────

const STEP_ICONS = [User, Activity, MessageSquare, Bell] as const;
const STEP_LABELS = ["Profile", "Vitals", "Ask AI", "Notifications"] as const;

function StepDots({ current }: { current: number }) {
  return (
    <div className="flex items-center gap-2 mb-6">
      {STEP_ICONS.map((Icon, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={i} className="flex flex-col items-center gap-1 flex-1">
            <div
              className={cn(
                "size-8 rounded-full flex items-center justify-center mx-auto transition-all",
                done
                  ? "bg-brand-600 text-white"
                  : active
                  ? "bg-brand-50 border-2 border-brand-600 text-brand-600"
                  : "bg-bg-subtle border border-border text-ink-muted",
              )}
            >
              {done ? <CheckCircle2 className="size-4" /> : <Icon className="size-3.5" />}
            </div>
            <span
              className={cn(
                "text-[10px] font-medium",
                active ? "text-brand-600" : done ? "text-brand-500" : "text-ink-muted",
              )}
            >
              {STEP_LABELS[i]}
            </span>
          </div>
        );
      })}
    </div>
  );
}

// ── Shared field wrapper ──────────────────────────────────────────────────────

function Field({
  label,
  optional,
  children,
}: {
  label: string;
  optional?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-ink mb-1.5">
        {label}
        {optional && <span className="ml-1 font-normal text-ink-subtle">(optional)</span>}
      </label>
      {children}
    </div>
  );
}

const inputCls =
  "w-full px-3 py-2 rounded-lg border border-border bg-bg text-sm text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent";

const textareaCls = inputCls + " resize-none";

function ActionRow({
  onSkip,
  children,
}: {
  onSkip?: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between pt-2">
      {onSkip ? (
        <button
          type="button"
          onClick={onSkip}
          className="text-sm text-ink-muted hover:text-ink transition-colors"
        >
          Skip for now
        </button>
      ) : (
        <span />
      )}
      {children}
    </div>
  );
}

// ── Step 1: Profile ───────────────────────────────────────────────────────────

function ProfileStep({
  profile,
  onNext,
  onSkip,
}: {
  profile: PatientProfile | null;
  onNext: () => void;
  onSkip: () => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    full_name: profile?.full_name ?? "",
    date_of_birth: profile?.date_of_birth ?? "",
    allergies: profile?.allergies ?? "",
    current_medications: profile?.current_medications ?? "",
    emergency_contact: profile?.emergency_contact ?? "",
  });
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => endpoints.updateProfile(form),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["patient-profile", "me"] });
      onNext();
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  function set(key: keyof typeof form, val: string) {
    setForm((p) => ({ ...p, [key]: val }));
  }

  return (
    <div className="space-y-3">
      <Field label="Full name">
        <input
          className={inputCls}
          value={form.full_name}
          onChange={(e) => set("full_name", e.target.value)}
          placeholder="Your full name"
        />
      </Field>
      <Field label="Date of birth" optional>
        <input
          type="date"
          className={inputCls}
          value={form.date_of_birth ?? ""}
          onChange={(e) => set("date_of_birth", e.target.value)}
          max={new Date().toISOString().slice(0, 10)}
        />
      </Field>
      <Field label="Known allergies" optional>
        <textarea
          className={textareaCls}
          rows={2}
          value={form.allergies}
          onChange={(e) => set("allergies", e.target.value)}
          placeholder="e.g. Penicillin, Peanuts"
        />
      </Field>
      <Field label="Current medications" optional>
        <textarea
          className={textareaCls}
          rows={2}
          value={form.current_medications}
          onChange={(e) => set("current_medications", e.target.value)}
          placeholder="e.g. Metformin 500 mg, Lisinopril 10 mg"
        />
      </Field>
      <Field label="Emergency contact" optional>
        <input
          className={inputCls}
          value={form.emergency_contact ?? ""}
          onChange={(e) => set("emergency_contact", e.target.value)}
          placeholder="Name and phone number"
        />
      </Field>

      {error && <p className="text-xs text-danger-600">{error}</p>}

      <ActionRow onSkip={onSkip}>
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
          Save & continue
          <ChevronRight className="size-4" />
        </Button>
      </ActionRow>
    </div>
  );
}

// ── Step 2: Vitals ────────────────────────────────────────────────────────────

const VITAL_FIELDS = [
  { key: "heart_rate", label: "Heart rate", unit: "bpm", placeholder: "72" },
  { key: "bp_sys", label: "Systolic BP", unit: "mmHg", placeholder: "120" },
  { key: "bp_dia", label: "Diastolic BP", unit: "mmHg", placeholder: "80" },
  { key: "temperature", label: "Temperature", unit: "°C", placeholder: "37.0" },
  { key: "oxygen_saturation", label: "Oxygen sat.", unit: "%", placeholder: "98" },
] as const;

type VitalKey = (typeof VITAL_FIELDS)[number]["key"];

function VitalsStep({
  patientId,
  onNext,
  onSkip,
}: {
  patientId: string;
  onNext: () => void;
  onSkip: () => void;
}) {
  const qc = useQueryClient();
  const [form, setForm] = useState<Record<VitalKey, string>>({
    heart_rate: "",
    bp_sys: "",
    bp_dia: "",
    temperature: "",
    oxygen_saturation: "",
  });
  const [error, setError] = useState<string | null>(null);

  function toNum(s: string): number | undefined {
    const n = Number(s);
    return s && Number.isFinite(n) ? n : undefined;
  }

  const mutation = useMutation({
    mutationFn: () =>
      endpoints.storeVitals({
        patient_id: patientId,
        heart_rate: toNum(form.heart_rate),
        blood_pressure_systolic: toNum(form.bp_sys),
        blood_pressure_diastolic: toNum(form.bp_dia),
        temperature: toNum(form.temperature),
        oxygen_saturation: toNum(form.oxygen_saturation),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["vitals-history", patientId] });
      onNext();
    },
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  const hasAny = Object.values(form).some((v) => v !== "");

  return (
    <div className="space-y-3">
      <p className="text-sm text-ink-muted">
        Enter any readings you have. You don&apos;t need all of them.
      </p>
      <div className="grid grid-cols-2 gap-3">
        {VITAL_FIELDS.map(({ key, label, unit, placeholder }) => (
          <div key={key}>
            <label className="block text-xs font-medium text-ink mb-1">
              {label}{" "}
              <span className="font-normal text-ink-subtle">({unit})</span>
            </label>
            <input
              type="number"
              className={inputCls}
              value={form[key]}
              onChange={(e) => setForm((p) => ({ ...p, [key]: e.target.value }))}
              placeholder={placeholder}
            />
          </div>
        ))}
      </div>

      {error && <p className="text-xs text-danger-600">{error}</p>}

      <ActionRow onSkip={onSkip}>
        <Button
          onClick={() => (hasAny ? mutation.mutate() : onNext())}
          disabled={mutation.isPending}
        >
          {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
          {hasAny ? "Record & continue" : "Continue"}
          <ChevronRight className="size-4" />
        </Button>
      </ActionRow>
    </div>
  );
}

// ── Step 3: Ask the AI ────────────────────────────────────────────────────────

const SAMPLE_QUESTIONS = [
  "What are normal blood pressure ranges?",
  "What causes a high resting heart rate?",
  "Tips for better sleep quality",
];

function AskAIStep({ onNext }: { onNext: () => void }) {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: () => endpoints.sendChat({ message: question }),
    onSuccess: (data) => setResponse(data.response),
    onError: (err) => setError(getApiErrorMessage(err)),
  });

  if (response !== null) {
    return (
      <div className="space-y-3">
        <div className="rounded-xl bg-bg-subtle border border-border p-4 text-sm text-ink max-h-48 overflow-y-auto prose-sm">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{response}</ReactMarkdown>
        </div>
        <p className="text-xs text-ink-muted text-center">
          The full AI assistant (with your health history) is in the Chat tab.
        </p>
        <ActionRow>
          <Button onClick={onNext}>
            Continue
            <ChevronRight className="size-4" />
          </Button>
        </ActionRow>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-ink-muted">Try a question or pick one below:</p>
      <div className="flex flex-wrap gap-1.5">
        {SAMPLE_QUESTIONS.map((q) => (
          <button
            key={q}
            type="button"
            onClick={() => setQuestion(q)}
            className={cn(
              "px-2.5 py-1 rounded-full text-xs border transition-colors",
              question === q
                ? "border-brand-400 bg-brand-50 text-brand-700"
                : "border-border text-ink-muted hover:border-brand-300 hover:text-ink",
            )}
          >
            {q}
          </button>
        ))}
      </div>
      <textarea
        className={textareaCls}
        rows={3}
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Type your health question…"
      />
      {error && <p className="text-xs text-danger-600">{error}</p>}
      <ActionRow onSkip={onNext}>
        <Button
          onClick={() => mutation.mutate()}
          disabled={!question.trim() || mutation.isPending}
        >
          {mutation.isPending ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Sparkles className="size-4" />
          )}
          Ask the AI
        </Button>
      </ActionRow>
    </div>
  );
}

// ── Step 4: Notifications ─────────────────────────────────────────────────────

const NOTIF_ITEMS = [
  {
    key: "vitals_reminders",
    label: "Vitals check-in reminders",
    desc: "Daily reminder to log your readings",
  },
  {
    key: "medication_reminders",
    label: "Medication reminders",
    desc: "Alerts for your scheduled medications",
  },
  {
    key: "appointment_reminders",
    label: "Appointment reminders",
    desc: "Notifications for upcoming appointments",
  },
  {
    key: "ai_health_tips",
    label: "AI health tips",
    desc: "Weekly personalised health insights",
  },
] as const;

type NotifKey = (typeof NOTIF_ITEMS)[number]["key"];

function NotificationsStep({ onFinish }: { onFinish: () => void }) {
  const [prefs, setPrefs] = useState<Record<NotifKey, boolean>>({
    vitals_reminders: true,
    medication_reminders: true,
    appointment_reminders: true,
    ai_health_tips: false,
  });

  function toggle(key: NotifKey) {
    setPrefs((p) => ({ ...p, [key]: !p[key] }));
  }

  function finish() {
    try {
      localStorage.setItem("medi.notif_prefs", JSON.stringify(prefs));
    } catch {
      // ignore storage errors
    }
    onFinish();
  }

  return (
    <div className="space-y-3">
      {NOTIF_ITEMS.map(({ key, label, desc }) => (
        <button
          key={key}
          type="button"
          onClick={() => toggle(key)}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-xl border border-border bg-bg-elevated hover:border-brand-200 transition-colors text-left"
        >
          <div
            className={cn(
              "size-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors",
              prefs[key]
                ? "border-brand-600 bg-brand-600"
                : "border-border bg-bg",
            )}
          >
            {prefs[key] && <CheckCircle2 className="size-3 text-white" />}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-ink">{label}</p>
            <p className="text-xs text-ink-muted">{desc}</p>
          </div>
        </button>
      ))}
      <ActionRow>
        <Button onClick={finish}>
          Get started
          <ChevronRight className="size-4" />
        </Button>
      </ActionRow>
    </div>
  );
}

// ── Main wizard ───────────────────────────────────────────────────────────────

const STEP_META = [
  {
    title: "Welcome! Let's set up your profile",
    desc: "This helps the AI personalise health guidance for you.",
  },
  {
    title: "Record your first vitals",
    desc: "Get an instant AI analysis of your current health status.",
  },
  {
    title: "Try the AI assistant",
    desc: "Ask anything about your health — it's private and personalised.",
  },
  {
    title: "Stay on top of your health",
    desc: "Set your notification preferences to build healthy habits.",
  },
];

export function OnboardingWizard({
  profile,
  onComplete,
}: {
  profile: PatientProfile | null;
  onComplete: () => void;
}) {
  const [step, setStep] = useState(0);
  const next = () => setStep((s) => Math.min(s + 1, 3));

  const { title, desc } = STEP_META[step];

  function stepContent() {
    switch (step) {
      case 0:
        return (
          <ProfileStep profile={profile} onNext={next} onSkip={next} />
        );
      case 1:
        return profile?.id ? (
          <VitalsStep patientId={profile.id} onNext={next} onSkip={next} />
        ) : (
          <div className="py-6 text-center space-y-4">
            <p className="text-sm text-ink-muted">
              Complete your profile first to enable vitals tracking.
            </p>
            <Button onClick={next}>Continue</Button>
          </div>
        );
      case 2:
        return <AskAIStep onNext={next} />;
      case 3:
        return <NotificationsStep onFinish={onComplete} />;
      default:
        return null;
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-lg rounded-2xl border border-border bg-bg shadow-2xl flex flex-col max-h-[90vh]">
        <div className="px-6 pt-6 pb-4 border-b border-border shrink-0">
          <StepDots current={step} />
          <h2 className="text-lg font-semibold text-ink">{title}</h2>
          <p className="text-sm text-ink-muted mt-0.5">{desc}</p>
        </div>
        <div className="p-6 overflow-y-auto">{stepContent()}</div>
      </div>
    </div>
  );
}
