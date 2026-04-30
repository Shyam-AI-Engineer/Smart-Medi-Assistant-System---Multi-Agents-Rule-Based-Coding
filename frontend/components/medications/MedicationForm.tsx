"use client";

import { useState } from "react";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import type { MedicationPayload } from "@/lib/api";

interface MedicationFormProps {
  onSubmit: (payload: MedicationPayload) => Promise<void>;
  onCancel: () => void;
  loading?: boolean;
}

const EMPTY: MedicationPayload = {
  medication_name: "",
  dosage: "",
  frequency: "",
  start_date: new Date().toISOString().split("T")[0],
  end_date: null,
  notes: null,
};

export function MedicationForm({ onSubmit, onCancel, loading }: MedicationFormProps) {
  const [form, setForm] = useState<MedicationPayload>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof MedicationPayload, string>>>({});

  function set(key: keyof MedicationPayload, value: string | null) {
    setForm((f) => ({ ...f, [key]: value || null }));
    setErrors((e) => ({ ...e, [key]: undefined }));
  }

  function validate(): boolean {
    const next: typeof errors = {};
    if (!form.medication_name?.trim()) next.medication_name = "Required";
    if (!form.dosage?.trim()) next.dosage = "Required";
    if (!form.frequency?.trim()) next.frequency = "Required";
    if (!form.start_date) next.start_date = "Required";
    if (form.end_date && form.start_date && form.end_date < form.start_date) {
      next.end_date = "Must be after start date";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit({
      ...form,
      medication_name: form.medication_name!.trim(),
      dosage: form.dosage!.trim(),
      frequency: form.frequency!.trim(),
    });
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input
        label="Medication name"
        placeholder="e.g. Metformin"
        value={form.medication_name ?? ""}
        onChange={(e) => set("medication_name", e.target.value)}
        error={errors.medication_name}
        autoFocus
      />
      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Dosage"
          placeholder="e.g. 500 mg"
          value={form.dosage ?? ""}
          onChange={(e) => set("dosage", e.target.value)}
          error={errors.dosage}
        />
        <Input
          label="Frequency"
          placeholder="e.g. Twice daily"
          value={form.frequency ?? ""}
          onChange={(e) => set("frequency", e.target.value)}
          error={errors.frequency}
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Input
          label="Start date"
          type="date"
          value={form.start_date ?? ""}
          onChange={(e) => set("start_date", e.target.value)}
          error={errors.start_date}
        />
        <Input
          label="End date (optional)"
          type="date"
          value={form.end_date ?? ""}
          onChange={(e) => set("end_date", e.target.value || null)}
          error={errors.end_date}
        />
      </div>
      <Textarea
        label="Notes (optional)"
        placeholder="Any additional notes…"
        value={form.notes ?? ""}
        onChange={(e) => set("notes", e.target.value)}
        className="min-h-[72px]"
      />
      <div className="flex gap-2 pt-1">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={loading}>
          Cancel
        </Button>
        <Button type="submit" loading={loading}>
          Add medication
        </Button>
      </div>
    </form>
  );
}
