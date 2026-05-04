"use client";

import { useState, useMemo } from "react";
import { ShieldCheck, Search, AlertTriangle, Users, Activity, X } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Loader } from "@/components/ui/Loader";
import { useAuditLogs, useAuditLogsSummary } from "@/hooks/useAdminAnalytics";
import type { AuditLogItem } from "@/lib/api";

// ── Helpers ───────────────────────────────────────────────────────────────────

const ACTION_LABELS: Record<string, string> = {
  login: "Login",
  register: "Register",
  view_patient: "View Patient",
  record_vitals: "Record Vitals",
  view_vitals: "View Vitals",
  send_chat: "Send Chat",
  view_chat_history: "View Chat History",
  export_pdf: "Export PDF",
  view_audit_logs: "View Audit Logs",
};

type ActionTone = "brand" | "success" | "warning" | "danger" | "neutral";

function actionTone(action: string): ActionTone {
  if (action === "login" || action === "register") return "brand";
  if (action === "record_vitals") return "success";
  if (action.startsWith("view_")) return "warning";
  if (action === "export_pdf") return "neutral";
  return "neutral";
}

function roleTone(role: string): ActionTone {
  if (role === "admin") return "danger";
  if (role === "doctor") return "brand";
  if (role === "patient") return "success";
  return "neutral";
}

function fmtTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

// ── Summary KPI card ──────────────────────────────────────────────────────────

function KpiCard({
  icon,
  label,
  value,
  sub,
  danger,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
  danger?: boolean;
}) {
  return (
    <Card>
      <CardContent className="p-5 flex items-start gap-4">
        <div
          className={`size-10 rounded-lg flex items-center justify-center shrink-0 ${
            danger ? "bg-danger-50 text-danger-600" : "bg-brand-50 text-brand-600"
          }`}
        >
          {icon}
        </div>
        <div>
          <p className="text-xs text-ink-subtle uppercase font-medium tracking-wide">{label}</p>
          <p className={`text-2xl font-bold ${danger ? "text-danger-600" : "text-ink"}`}>
            {value}
          </p>
          {sub && <p className="text-xs text-ink-muted mt-0.5">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

// ── Row ───────────────────────────────────────────────────────────────────────

function AuditRow({ row }: { row: AuditLogItem }) {
  const [expanded, setExpanded] = useState(false);
  const label = ACTION_LABELS[row.action] ?? row.action;

  return (
    <>
      <tr
        className="hover:bg-bg-subtle/40 transition-colors cursor-pointer"
        onClick={() => setExpanded((p) => !p)}
      >
        <td className="px-4 py-2.5 text-xs text-ink-muted whitespace-nowrap">
          {fmtTime(row.created_at)}
        </td>
        <td className="px-4 py-2.5">
          <p className="text-sm text-ink font-medium">{row.user_email}</p>
          <Badge tone={roleTone(row.user_role)} className="text-[10px] mt-0.5">
            {row.user_role}
          </Badge>
        </td>
        <td className="px-4 py-2.5">
          <Badge tone={actionTone(row.action)}>{label}</Badge>
        </td>
        <td className="px-4 py-2.5 text-sm text-ink-muted">
          <span className="font-medium text-ink">{row.resource_type}</span>
          {row.resource_id && (
            <span className="ml-1.5 font-mono text-[10px] text-ink-subtle">
              {row.resource_id.slice(0, 8)}…
            </span>
          )}
        </td>
        <td className="px-4 py-2.5">
          <Badge tone={row.outcome === "failure" ? "danger" : "success"}>
            {row.outcome}
          </Badge>
        </td>
        <td className="px-4 py-2.5 text-xs text-ink-muted font-mono">
          {row.ip_address ?? "—"}
        </td>
      </tr>
      {expanded && (
        <tr className="bg-bg-subtle/60">
          <td colSpan={6} className="px-6 py-3 text-xs text-ink-muted space-y-1">
            <p>
              <span className="font-semibold text-ink">User ID:</span> {row.user_id}
            </p>
            {row.resource_id && (
              <p>
                <span className="font-semibold text-ink">Resource ID:</span> {row.resource_id}
              </p>
            )}
            {row.details && (
              <p>
                <span className="font-semibold text-ink">Details:</span> {row.details}
              </p>
            )}
            <p>
              <span className="font-semibold text-ink">Event ID:</span>{" "}
              <span className="font-mono">{row.id}</span>
            </p>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const ACTION_OPTIONS = [
  { value: "", label: "All actions" },
  { value: "login", label: "Login" },
  { value: "register", label: "Register" },
  { value: "view_patient", label: "View Patient" },
  { value: "record_vitals", label: "Record Vitals" },
  { value: "export_pdf", label: "Export PDF" },
  { value: "view_audit_logs", label: "View Audit Logs" },
];

const RESOURCE_OPTIONS = [
  { value: "", label: "All resources" },
  { value: "auth", label: "Auth" },
  { value: "patient", label: "Patient" },
  { value: "vitals", label: "Vitals" },
  { value: "chat", label: "Chat" },
  { value: "admin", label: "Admin" },
];

const DATE_PRESETS = [
  { label: "Last 7 days", days: 7 },
  { label: "Last 30 days", days: 30 },
  { label: "Last 90 days", days: 90 },
];

export default function AuditLogsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [resourceType, setResourceType] = useState("");
  const [outcome, setOutcome] = useState("");
  const [summaryDays, setSummaryDays] = useState(30);

  // Debounce search so we don't fire on every keystroke
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [searchTimer, setSearchTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  function handleSearchChange(val: string) {
    setSearch(val);
    if (searchTimer) clearTimeout(searchTimer);
    const t = setTimeout(() => {
      setDebouncedSearch(val);
      setPage(1);
    }, 400);
    setSearchTimer(t);
  }

  function clearFilters() {
    setSearch("");
    setDebouncedSearch("");
    setAction("");
    setResourceType("");
    setOutcome("");
    setPage(1);
  }

  const queryParams = useMemo(
    () => ({
      page,
      limit: 50,
      ...(debouncedSearch ? { search: debouncedSearch } : {}),
      ...(action ? { action } : {}),
      ...(resourceType ? { resource_type: resourceType } : {}),
      ...(outcome ? { outcome } : {}),
    }),
    [page, debouncedSearch, action, resourceType, outcome],
  );

  const { data, isLoading } = useAuditLogs(queryParams);
  const { data: summary } = useAuditLogsSummary(summaryDays);

  const hasActiveFilter = search || action || resourceType || outcome;
  const totalPages = data ? Math.ceil(data.total / 50) : 1;

  const selectCls =
    "h-8 px-2 rounded-md border border-border bg-bg text-sm text-ink outline-none focus:border-brand-500 transition-colors";

  return (
    <div className="container py-8 max-w-7xl">
      <PageHeader
        title="Audit Logs"
        description="Complete trail of who accessed patient data and when."
        actions={
          <div className="flex items-center gap-2">
            {DATE_PRESETS.map((p) => (
              <button
                key={p.days}
                onClick={() => setSummaryDays(p.days)}
                className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                  summaryDays === p.days
                    ? "border-brand-500 bg-brand-50 text-brand-700"
                    : "border-border text-ink-muted hover:text-ink"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        }
      />

      {/* KPI strip */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KpiCard
          icon={<Activity className="size-5" />}
          label="Total Events"
          value={summary?.total_events?.toLocaleString() ?? "—"}
          sub={`Last ${summaryDays} days`}
        />
        <KpiCard
          icon={<Users className="size-5" />}
          label="Unique Users"
          value={summary?.unique_users ?? "—"}
          sub="Active in period"
        />
        <KpiCard
          icon={<AlertTriangle className="size-5" />}
          label="Failed Attempts"
          value={summary?.failures ?? "—"}
          sub="Login failures & errors"
          danger={(summary?.failures ?? 0) > 0}
        />
      </div>

      {/* Action breakdown table */}
      {summary && summary.breakdown.length > 0 && (
        <Card className="mt-5">
          <CardHeader>
            <CardTitle>Activity Breakdown</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-bg-subtle/60 text-ink-muted">
                  <tr className="text-left">
                    <th className="px-5 py-2.5 font-medium">Action</th>
                    <th className="px-5 py-2.5 font-medium text-right">Success</th>
                    <th className="px-5 py-2.5 font-medium text-right">Failure</th>
                    <th className="px-5 py-2.5 font-medium text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {summary.breakdown.map((b) => (
                    <tr key={b.action} className="hover:bg-bg-subtle/40">
                      <td className="px-5 py-2">
                        <Badge tone={actionTone(b.action)}>
                          {ACTION_LABELS[b.action] ?? b.action}
                        </Badge>
                      </td>
                      <td className="px-5 py-2 text-right text-success-600 font-medium">
                        {b.success}
                      </td>
                      <td className="px-5 py-2 text-right text-danger-600 font-medium">
                        {b.failure || "—"}
                      </td>
                      <td className="px-5 py-2 text-right font-semibold text-ink">
                        {b.total}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filter bar */}
      <div className="mt-6 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-ink-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Search by email…"
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full h-8 pl-8 pr-3 rounded-md border border-border bg-bg text-sm text-ink placeholder:text-ink-subtle outline-none focus:border-brand-500 transition-colors"
          />
        </div>

        <select
          value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }}
          className={selectCls}
        >
          {ACTION_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <select
          value={resourceType}
          onChange={(e) => { setResourceType(e.target.value); setPage(1); }}
          className={selectCls}
        >
          {RESOURCE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <select
          value={outcome}
          onChange={(e) => { setOutcome(e.target.value); setPage(1); }}
          className={selectCls}
        >
          <option value="">All outcomes</option>
          <option value="success">Success</option>
          <option value="failure">Failure</option>
        </select>

        {hasActiveFilter && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="size-3.5" /> Clear
          </Button>
        )}
      </div>

      {/* Log table */}
      <Card className="mt-4">
        {isLoading ? (
          <div className="py-16">
            <Loader label="Loading audit trail…" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="py-16 text-center">
            <ShieldCheck className="size-8 text-ink-subtle mx-auto mb-3" />
            <p className="text-sm font-medium text-ink">No events found</p>
            <p className="text-xs text-ink-muted mt-1">
              {hasActiveFilter ? "Try adjusting your filters." : "Audit events will appear here once users start logging in."}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-bg-subtle/60 text-ink-muted border-b border-border">
                  <tr className="text-left">
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Timestamp (UTC)</th>
                    <th className="px-4 py-3 font-medium">User</th>
                    <th className="px-4 py-3 font-medium">Action</th>
                    <th className="px-4 py-3 font-medium">Resource</th>
                    <th className="px-4 py-3 font-medium">Outcome</th>
                    <th className="px-4 py-3 font-medium">IP Address</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.items.map((row) => (
                    <AuditRow key={row.id} row={row} />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-4 py-3 border-t border-border flex items-center justify-between text-sm">
              <p className="text-ink-muted">
                Showing{" "}
                <span className="font-medium text-ink">
                  {(page - 1) * 50 + 1}–{Math.min(page * 50, data.total)}
                </span>{" "}
                of{" "}
                <span className="font-medium text-ink">{data.total.toLocaleString()}</span>{" "}
                events
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  Previous
                </Button>
                <span className="text-ink-muted text-xs">
                  {page} / {totalPages}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!data.has_next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
