"use client";

import { useState } from "react";
import { Pill, Trash2, AlertTriangle, CheckCircle, ShieldAlert, ChevronDown, ChevronUp } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { Card, CardContent } from "@/components/ui/Card";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { MedicationForm } from "@/components/medications/MedicationForm";
import { useMedications, useAddMedication, useDeleteMedication, useCheckInteractions } from "@/hooks/useMedications";
import { getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { MedicationPayload } from "@/lib/api";

function riskBadge(level: string) {
  switch (level.toUpperCase()) {
    case "NONE": return <Badge tone="success">No interactions found</Badge>;
    case "LOW": return <Badge tone="brand">Low risk</Badge>;
    case "MODERATE": return <Badge tone="warning">Moderate risk</Badge>;
    case "HIGH": return <Badge tone="danger">High risk</Badge>;
    case "CRITICAL": return <Badge tone="danger">Critical risk</Badge>;
    default: return <Badge tone="neutral">{level}</Badge>;
  }
}

export default function MedicationsPage() {
  const { data, isLoading } = useMedications();
  const addMutation = useAddMedication();
  const deleteMutation = useDeleteMedication();
  const interactionQuery = useCheckInteractions();

  const [modalOpen, setModalOpen] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [showInteractions, setShowInteractions] = useState(false);

  const medications = data?.items ?? [];
  const isEmpty = !isLoading && medications.length === 0;
  const interactions = interactionQuery.data;

  async function handleAdd(payload: MedicationPayload) {
    try {
      setAddError(null);
      await addMutation.mutateAsync(payload);
      setModalOpen(false);
    } catch (err) {
      setAddError(getApiErrorMessage(err));
    }
  }

  async function handleDelete(id: string) {
    try {
      await deleteMutation.mutateAsync(id);
      setDeleteConfirm(null);
    } catch (err) {
      console.error("Delete failed:", err);
    }
  }

  function handleCheckInteractions() {
    setShowInteractions(true);
    interactionQuery.refetch();
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Medications"
        description="Track your current medications and check for drug interactions"
        actions={
          <div className="flex gap-2">
            {medications.length >= 2 && (
              <Button
                variant="secondary"
                onClick={handleCheckInteractions}
                loading={interactionQuery.isFetching}
              >
                <AlertTriangle className="size-4" />
                Check Interactions
              </Button>
            )}
            <Button onClick={() => { setAddError(null); setModalOpen(true); }}>
              <Pill className="size-4" />
              Add Medication
            </Button>
          </div>
        }
      />

      {/* Interaction results panel */}
      {showInteractions && interactions && (
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-ink">Interaction Check</span>
                {riskBadge(interactions.risk_level)}
              </div>
              <button
                onClick={() => setShowInteractions(false)}
                className="text-ink-muted hover:text-ink transition-colors"
              >
                <ChevronUp className="size-4" />
              </button>
            </div>

            <p className="text-sm text-ink leading-relaxed mb-3">{interactions.patient_response}</p>

            {interactions.contraindications.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-medium text-danger-700 mb-1">Contraindications</p>
                <ul className="space-y-0.5">
                  {interactions.contraindications.map((c, i) => (
                    <li key={i} className="text-xs text-danger-600 flex items-start gap-1.5">
                      <AlertTriangle className="size-3 shrink-0 mt-0.5" />{c}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {interactions.warning_signs.length > 0 && (
              <div className="mb-2">
                <p className="text-xs font-medium text-warning-700 mb-1">Warning signs to watch</p>
                <ul className="space-y-0.5">
                  {interactions.warning_signs.map((w, i) => (
                    <li key={i} className="text-xs text-warning-600 flex items-start gap-1.5">
                      <ChevronDown className="size-3 shrink-0 mt-0.5" />{w}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {interactions.disclaimer && (
              <div className="mt-3 flex items-start gap-2 px-3 py-2 rounded-md bg-warning-50 border border-warning-100 text-xs text-warning-700">
                <ShieldAlert className="size-4 mt-0.5 shrink-0" />
                <span>{interactions.disclaimer}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader size="lg" label="Loading medications…" />
        </div>
      ) : isEmpty ? (
        <EmptyState
          icon={<Pill className="size-6 text-brand-500" />}
          title="No medications logged"
          description="Add your current medications so the AI can provide personalized guidance and check for drug interactions."
          action={
            <Button onClick={() => { setAddError(null); setModalOpen(true); }}>
              Add your first medication
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {medications.map((med) => (
            <Card key={med.id}>
              <CardContent className="pt-4">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-sm text-ink">{med.medication_name}</p>
                    <p className="text-xs text-ink-muted mt-0.5">
                      {med.dosage} · {med.frequency}
                    </p>
                  </div>
                  <button
                    onClick={() => setDeleteConfirm(med.id)}
                    disabled={deleteMutation.isPending}
                    className={cn(
                      "p-1.5 rounded text-danger-600 hover:bg-danger-50 transition-colors shrink-0",
                      deleteMutation.isPending && "opacity-50 cursor-not-allowed",
                    )}
                    title="Remove medication"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </div>

                <div className="mt-3 flex flex-wrap gap-1.5 text-xs text-ink-muted">
                  <span>
                    Started {new Date(med.start_date).toLocaleDateString()}
                  </span>
                  {med.end_date && (
                    <>
                      <span>·</span>
                      <span>Until {new Date(med.end_date).toLocaleDateString()}</span>
                    </>
                  )}
                  {!med.end_date && (
                    <Badge tone="success" className="ml-auto">
                      <CheckCircle className="size-3 mr-1" />
                      Active
                    </Badge>
                  )}
                </div>

                {med.notes && (
                  <p className="mt-2 text-xs text-ink-muted border-t border-border pt-2">
                    {med.notes}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Add Medication">
        <MedicationForm
          onSubmit={handleAdd}
          onCancel={() => setModalOpen(false)}
          loading={addMutation.isPending}
        />
        {addError && (
          <p className="mt-2 text-xs text-danger-600">{addError}</p>
        )}
      </Modal>

      {deleteConfirm && (
        <Modal
          open={!!deleteConfirm}
          onClose={() => setDeleteConfirm(null)}
          title="Remove Medication"
        >
          <div className="space-y-4">
            <p className="text-sm text-ink">
              Are you sure you want to remove this medication from your list?
            </p>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={() => setDeleteConfirm(null)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={() => handleDelete(deleteConfirm)}
                loading={deleteMutation.isPending}
              >
                Remove
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
