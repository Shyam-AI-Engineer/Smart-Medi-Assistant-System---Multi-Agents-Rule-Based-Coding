"use client";

import { useState } from "react";
import { Heart, Activity, Wind, Thermometer, Wind as WindIcon, Scale } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/Card";
import { Input, Textarea } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";

export interface VitalsFormValues {
  heart_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  oxygen_saturation?: number;
  temperature?: number;
  respiratory_rate?: number;
  weight?: number;
  notes?: string;
}

interface VitalsFormProps {
  onSubmit: (values: VitalsFormValues) => void;
  loading?: boolean;
}

export function VitalsForm({ onSubmit, loading }: VitalsFormProps) {
  const [v, setV] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);

  function set(key: string, val: string) {
    setV((prev) => ({ ...prev, [key]: val }));
  }

  function toNum(s: string | undefined): number | undefined {
    if (s === undefined || s === "") return undefined;
    const n = Number(s);
    return Number.isFinite(n) ? n : undefined;
  }

  function handle(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const payload: VitalsFormValues = {
      heart_rate: toNum(v.heart_rate),
      blood_pressure_systolic: toNum(v.bp_sys),
      blood_pressure_diastolic: toNum(v.bp_dia),
      oxygen_saturation: toNum(v.spo2),
      temperature: toNum(v.temp),
      respiratory_rate: toNum(v.rr),
      weight: toNum(v.weight),
      notes: v.notes?.trim() || undefined,
    };

    const hasAny = Object.entries(payload).some(
      ([k, val]) => k !== "notes" && val !== undefined,
    );
    if (!hasAny) {
      setError("Enter at least one measurement.");
      return;
    }
    onSubmit(payload);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Record vitals</CardTitle>
        <CardDescription>
          Enter the measurements you have. Empty fields are skipped.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handle}>
        <CardContent className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input
              name="heart_rate"
              type="number"
              label="Heart rate"
              placeholder="72"
              suffix={<span className="text-xs">bpm</span>}
              prefix={<Heart className="size-4" />}
              min={20}
              max={300}
              value={v.heart_rate || ""}
              onChange={(e) => set("heart_rate", e.target.value)}
            />
            <Input
              name="spo2"
              type="number"
              label="Oxygen saturation"
              placeholder="98"
              suffix={<span className="text-xs">%</span>}
              prefix={<Wind className="size-4" />}
              min={50}
              max={100}
              step="0.1"
              value={v.spo2 || ""}
              onChange={(e) => set("spo2", e.target.value)}
            />
            <Input
              name="bp_sys"
              type="number"
              label="Systolic BP"
              placeholder="120"
              suffix={<span className="text-xs">mmHg</span>}
              prefix={<Activity className="size-4" />}
              min={50}
              max={300}
              value={v.bp_sys || ""}
              onChange={(e) => set("bp_sys", e.target.value)}
            />
            <Input
              name="bp_dia"
              type="number"
              label="Diastolic BP"
              placeholder="80"
              suffix={<span className="text-xs">mmHg</span>}
              prefix={<Activity className="size-4" />}
              min={30}
              max={200}
              value={v.bp_dia || ""}
              onChange={(e) => set("bp_dia", e.target.value)}
            />
            <Input
              name="temp"
              type="number"
              label="Temperature"
              placeholder="37.0"
              suffix={<span className="text-xs">°C</span>}
              prefix={<Thermometer className="size-4" />}
              min={30}
              max={45}
              step="0.1"
              value={v.temp || ""}
              onChange={(e) => set("temp", e.target.value)}
            />
            <Input
              name="rr"
              type="number"
              label="Respiratory rate"
              placeholder="16"
              suffix={<span className="text-xs">/ min</span>}
              prefix={<WindIcon className="size-4" />}
              min={4}
              max={60}
              value={v.rr || ""}
              onChange={(e) => set("rr", e.target.value)}
            />
            <Input
              name="weight"
              type="number"
              label="Weight"
              placeholder="70"
              suffix={<span className="text-xs">kg</span>}
              prefix={<Scale className="size-4" />}
              min={1}
              max={500}
              step="0.1"
              value={v.weight || ""}
              onChange={(e) => set("weight", e.target.value)}
            />
          </div>

          <Textarea
            name="notes"
            label="Notes (optional)"
            placeholder="Any context — e.g. taken after exercise, feeling dizzy…"
            maxLength={500}
            value={v.notes || ""}
            onChange={(e) => set("notes", e.target.value)}
          />

          {error && (
            <p className="text-sm text-danger-600">{error}</p>
          )}
        </CardContent>
        <CardFooter className="flex justify-end">
          <Button type="submit" loading={loading} size="md">
            Submit & analyze
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
