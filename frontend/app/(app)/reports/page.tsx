"use client";

import { useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card, CardContent, CardFooter } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Modal } from "@/components/ui/Modal";
import { EmptyState } from "@/components/ui/EmptyState";
import { Loader } from "@/components/ui/Loader";
import { useReports, useUploadReport, useDeleteReport } from "@/hooks/useReports";
import { useMyPatientProfile } from "@/hooks/useVitals";
import { ReportUploadZone } from "@/components/reports/ReportUploadZone";
import { getApiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

export default function ReportsPage() {
  const { data: profile } = useMyPatientProfile();
  const { data: reportsData, isLoading } = useReports(profile?.id);
  const uploadMutation = useUploadReport();
  const deleteMutation = useDeleteReport();

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!selectedFile) {
      setUploadError("Please select a file");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setUploadError("File is too large (max 10 MB)");
      return;
    }

    try {
      setUploadError(null);
      await uploadMutation.mutateAsync(selectedFile);
      setSelectedFile(null);
      setModalOpen(false);
    } catch (err) {
      setUploadError(getApiErrorMessage(err));
    }
  };

  const handleDelete = async (reportId: string) => {
    try {
      await deleteMutation.mutateAsync(reportId);
      setDeleteConfirm(null);
    } catch (err) {
      console.error("Failed to delete report:", err);
    }
  };

  const reports = reportsData?.items ?? [];
  const isEmpty = reports.length === 0 && !isLoading;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "processing":
        return <Badge tone="warning">Processing</Badge>;
      case "done":
        return <Badge tone="success">Ready</Badge>;
      case "error":
        return <Badge tone="danger">Error</Badge>;
      default:
        return <Badge tone="neutral">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Medical Reports"
        description="Upload lab results, discharge summaries, and other medical documents"
        actions={
          <Button
            onClick={() => {
              setSelectedFile(null);
              setUploadError(null);
              setModalOpen(true);
            }}
          >
            Upload Report
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader size="lg" label="Loading reports..." />
        </div>
      ) : isEmpty ? (
        <EmptyState
          icon={<FileText className="size-6 text-brand-500" />}
          title="No reports yet"
          description="Upload your lab results, discharge summaries, or other medical documents. The AI will reference them when answering your questions."
          action={
            <Button
              onClick={() => {
                setSelectedFile(null);
                setUploadError(null);
                setModalOpen(true);
              }}
            >
              Upload your first report
            </Button>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {reports.map((report) => (
            <Card key={report.id}>
              <CardContent className="pt-4">
                <div className="space-y-3">
                  <div className="space-y-1">
                    <p className="font-medium text-sm truncate">{report.filename}</p>
                    <p className="text-xs text-ink-muted">
                      {new Date(report.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    <Badge tone="neutral">.{report.file_type}</Badge>
                    {getStatusBadge(report.status)}
                    {report.page_count && (
                      <Badge tone="neutral">{report.page_count} pages</Badge>
                    )}
                  </div>

                  {report.status === "error" && report.error_message && (
                    <div className="p-2 bg-danger-50 border border-danger-200 rounded text-xs text-danger-700">
                      {report.error_message}
                    </div>
                  )}

                  {report.text_preview && (
                    <p className="text-xs text-ink-muted line-clamp-2">
                      {report.text_preview}
                    </p>
                  )}
                </div>
              </CardContent>

              <CardFooter>
                <button
                  onClick={() => setDeleteConfirm(report.id)}
                  disabled={deleteMutation.isPending}
                  className={cn(
                    "ml-auto p-1.5 rounded text-danger-600 hover:bg-danger-50 transition-colors",
                    deleteMutation.isPending && "opacity-50 cursor-not-allowed"
                  )}
                  title="Delete report"
                >
                  <Trash2 className="size-4" />
                </button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Upload Medical Report">
        <div className="space-y-4">
          <ReportUploadZone
            onFileChange={setSelectedFile}
            selectedFile={selectedFile}
            error={uploadError}
          />
          <div className="flex gap-2 pt-2">
            <Button
              variant="secondary"
              onClick={() => setModalOpen(false)}
              disabled={uploadMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              loading={uploadMutation.isPending}
              disabled={!selectedFile}
            >
              Upload
            </Button>
          </div>
        </div>
      </Modal>

      {deleteConfirm && (
        <Modal
          open={!!deleteConfirm}
          onClose={() => setDeleteConfirm(null)}
          title="Delete Report"
        >
          <div className="space-y-4">
            <p className="text-sm text-ink">
              Are you sure you want to delete this report? This action cannot be undone, and the AI
              will no longer have access to this document.
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
                Delete
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
