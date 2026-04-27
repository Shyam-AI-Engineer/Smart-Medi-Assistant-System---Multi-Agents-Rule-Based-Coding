"use client";

import Link from "next/link";
import { useState, useMemo } from "react";
import { ChevronRight, Search } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Input } from "@/components/ui/Input";
import { Loader } from "@/components/ui/Loader";
import { EmptyState } from "@/components/ui/EmptyState";
import { useDoctorPatients } from "@/hooks/useDoctor";

const PATIENTS_PER_PAGE = 20;

export default function DoctorPatientsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const { data, isLoading } = useDoctorPatients(PATIENTS_PER_PAGE, 0);

  const patients = data?.items ?? [];

  // Filter patients by name or email
  const filteredPatients = useMemo(() => {
    if (!searchTerm.trim()) return patients;
    const term = searchTerm.toLowerCase();
    return patients.filter(
      (p) =>
        (p.full_name?.toLowerCase() ?? "").includes(term) ||
        (p.id?.toLowerCase() ?? "").includes(term),
    );
  }, [patients, searchTerm]);

  return (
    <div className="container py-8 max-w-5xl">
      <PageHeader
        title="All Patients"
        description="View and manage all patients in the system."
      />

      {/* Search bar */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-ink-muted" />
          <Input
            type="text"
            placeholder="Search by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="py-24">
          <Loader label="Loading patients…" />
        </div>
      ) : patients.length === 0 ? (
        <EmptyState
          title="No patients found"
          description="There are no patients in the system yet."
        />
      ) : filteredPatients.length === 0 ? (
        <EmptyState
          title="No matching patients"
          description={`No patients match "${searchTerm}"`}
        />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              Patients ({filteredPatients.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1 divide-y divide-border">
              {filteredPatients.map((patient) => (
                <Link
                  key={patient.id}
                  href={`/doctor/patients/${patient.id}`}
                  className="flex items-center justify-between p-4 -mx-6 px-6 hover:bg-bg-subtle transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-ink group-hover:text-brand-700 transition-colors">
                      {patient.full_name || "Unknown"}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      {patient.age && (
                        <span className="text-xs text-ink-subtle">Age {patient.age}</span>
                      )}
                      {patient.latest_vital_timestamp && (
                        <span className="text-xs text-ink-subtle">
                          • Last vitals{" "}
                          {new Date(patient.latest_vital_timestamp).toLocaleDateString(
                            undefined,
                            { month: "short", day: "numeric" },
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={
                        patient.latest_vital_status === "CRITICAL"
                          ? "danger"
                          : patient.latest_vital_status === "HIGH"
                            ? "warning"
                            : patient.latest_vital_status === "MODERATE"
                              ? "info"
                              : "success"
                      }
                    >
                      {patient.latest_vital_status}
                    </Badge>
                    <ChevronRight className="size-4 text-ink-muted group-hover:text-brand-700 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
