"use client";

import { AlertTriangle, Phone, PhoneCall } from "lucide-react";
import { cn } from "@/lib/cn";

export interface EscalationData {
  urgency_level: string;
  immediate_action?: string;
  emergency_contact?: string | null;
  emergency_number?: string;
}

function extractTelHref(contact: string): string | null {
  const digits = contact.replace(/[^\d+]/g, "");
  return digits.length >= 7 ? `tel:${digits}` : null;
}

export function EscalationCard({ urgency_level, immediate_action, emergency_contact, emergency_number }: EscalationData) {
  const isCritical = urgency_level === "critical";
  const dialNumber = emergency_number ?? "108";
  const telHref = emergency_contact ? extractTelHref(emergency_contact) : null;

  return (
    <div
      className={cn(
        "mt-3 rounded-xl border-2 p-4",
        isCritical
          ? "bg-danger-50 border-danger-300"
          : "bg-warning-50 border-warning-300",
      )}
      role="alert"
    >
      <div className="flex items-start gap-3 mb-3">
        <AlertTriangle
          className={cn(
            "size-5 shrink-0 mt-0.5",
            isCritical ? "text-danger-600" : "text-warning-600",
          )}
        />
        <div>
          <p
            className={cn(
              "text-sm font-bold",
              isCritical ? "text-danger-800" : "text-warning-800",
            )}
          >
            This may require urgent attention
          </p>
          <p
            className={cn(
              "text-xs mt-0.5 leading-relaxed",
              isCritical ? "text-danger-700" : "text-warning-700",
            )}
          >
            {immediate_action ||
              "Consider calling your doctor or emergency services immediately."}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <a
          href={`tel:${dialNumber}`}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-danger-600 text-white text-xs font-semibold hover:bg-danger-700 transition-colors"
        >
          <Phone className="size-3.5" />
          Call {dialNumber} (Ambulance)
        </a>

        {emergency_contact && telHref && (
          <a
            href={telHref}
            className={cn(
              "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold transition-colors",
              isCritical
                ? "border-danger-300 bg-danger-100 text-danger-800 hover:bg-danger-200"
                : "border-warning-400 bg-warning-100 text-warning-800 hover:bg-warning-200",
            )}
          >
            <PhoneCall className="size-3.5 shrink-0" />
            <span className="truncate max-w-[160px]">{emergency_contact}</span>
          </a>
        )}
      </div>
    </div>
  );
}
