"use client";

import { useState, useMemo } from "react";
import { Search, Users, Activity, X } from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Loader } from "@/components/ui/Loader";
import { useAdminUsers } from "@/hooks/useAdminAnalytics";
import { endpoints, getApiErrorMessage } from "@/lib/api";
import type { AdminUser } from "@/lib/api";

// ── Helpers ───────────────────────────────────────────────────────────────────

function roleTone(role: string): "brand" | "danger" | "success" | "warning" | "neutral" {
  if (role === "admin") return "danger";
  if (role === "doctor") return "brand";
  if (role === "patient") return "success";
  return "neutral";
}

function fmtDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

// ── KPI Card ──────────────────────────────────────────────────────────────────

function KpiCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <Card>
      <CardContent className="p-5 flex items-start gap-4">
        <div className="size-10 rounded-lg flex items-center justify-center shrink-0 bg-brand-50 text-brand-600">
          {icon}
        </div>
        <div>
          <p className="text-xs text-ink-subtle uppercase font-medium tracking-wide">{label}</p>
          <p className="text-2xl font-bold text-ink">{value}</p>
          {sub && <p className="text-xs text-ink-muted mt-0.5">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  );
}

// ── User Row ──────────────────────────────────────────────────────────────────

function UserRow({
  user,
  onDeactivate,
  onEdit,
}: {
  user: AdminUser;
  onDeactivate: (user: AdminUser) => void;
  onEdit: (user: AdminUser) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="hover:bg-bg-subtle/40 transition-colors"
        onClick={() => setExpanded((p) => !p)}
      >
        <td className="px-4 py-3">
          <p className="text-sm font-medium text-ink">{user.email}</p>
        </td>
        <td className="px-4 py-3 text-sm text-ink-muted">{user.full_name}</td>
        <td className="px-4 py-3">
          <Badge tone={roleTone(user.role)} className="capitalize">
            {user.role}
          </Badge>
        </td>
        <td className="px-4 py-3">
          <Badge tone={user.is_active ? "success" : "neutral"}>
            {user.is_active ? "Active" : "Inactive"}
          </Badge>
        </td>
        <td className="px-4 py-3 text-sm text-ink-muted whitespace-nowrap">
          {fmtDate(user.created_at)}
        </td>
        <td className="px-4 py-3">
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onEdit(user)}
            >
              Edit
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onDeactivate(user)}
            >
              {user.is_active ? "Deactivate" : "Reactivate"}
            </Button>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="bg-bg-subtle/60">
          <td colSpan={6} className="px-6 py-3 text-xs text-ink-muted space-y-1">
            <p>
              <span className="font-semibold text-ink">User ID:</span> {user.id}
            </p>
            <p>
              <span className="font-semibold text-ink">Role:</span> {user.role}
            </p>
            <p>
              <span className="font-semibold text-ink">Created:</span> {new Date(user.created_at).toLocaleString()}
            </p>
            <p>
              <span className="font-semibold text-ink">Updated:</span> {new Date(user.updated_at).toLocaleString()}
            </p>
          </td>
        </tr>
      )}
    </>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const ROLE_OPTIONS = [
  { value: "", label: "All roles" },
  { value: "patient", label: "Patient" },
  { value: "doctor", label: "Doctor" },
  { value: "admin", label: "Admin" },
];

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
];

export default function UsersPage() {
  const [offset, setOffset] = useState(0);
  const [search, setSearch] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editForm, setEditForm] = useState({ role: "", is_active: true });
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Debounce search
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [searchTimer, setSearchTimer] = useState<ReturnType<typeof setTimeout> | null>(null);

  function handleSearchChange(val: string) {
    setSearch(val);
    if (searchTimer) clearTimeout(searchTimer);
    const t = setTimeout(() => {
      setDebouncedSearch(val);
      setOffset(0);
    }, 400);
    setSearchTimer(t);
  }

  function clearFilters() {
    setSearch("");
    setDebouncedSearch("");
    setRole("");
    setStatus("");
    setOffset(0);
  }

  function handleEdit(user: AdminUser) {
    setEditingUser(user);
    setEditForm({ role: user.role, is_active: user.is_active });
    setShowEditModal(true);
  }

  async function handleDeactivate(user: AdminUser) {
    const action = user.is_active ? "Deactivate" : "Reactivate";
    if (!window.confirm(`${action} ${user.email}?`)) return;

    try {
      await endpoints.updateAdminUser(user.id, { is_active: !user.is_active });
      // Refetch the list by resetting offset
      setOffset(offset);
    } catch (err) {
      const msg = getApiErrorMessage(err, `Failed to ${action.toLowerCase()} user`);
      alert(msg);
    }
  }

  async function handleSaveEdit() {
    if (!editingUser) return;
    setIsSubmitting(true);
    try {
      await endpoints.updateAdminUser(editingUser.id, {
        role: editForm.role,
        is_active: editForm.is_active,
      });
      setShowEditModal(false);
      // Refetch the list
      setOffset(offset);
    } catch (err) {
      const msg = getApiErrorMessage(err, "Failed to update user");
      alert(msg);
    } finally {
      setIsSubmitting(false);
    }
  }

  const limit = 50;
  const { data, isLoading } = useAdminUsers(limit, offset, debouncedSearch, role);

  const hasActiveFilter = search || role || status;
  const filteredUsers = !status
    ? data?.items ?? []
    : (data?.items ?? []).filter((u) => {
        if (status === "active") return u.is_active;
        if (status === "inactive") return !u.is_active;
        return true;
      });

  const selectCls =
    "h-8 px-2 rounded-md border border-border bg-bg text-sm text-ink outline-none focus:border-brand-500 transition-colors";

  return (
    <div className="container py-8 max-w-7xl">
      <PageHeader
        title="Users"
        description="Manage system users, roles, and access status."
      />

      {/* KPI strip */}
      <div className="mt-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <KpiCard
          icon={<Users className="size-5" />}
          label="Total Users"
          value={data?.total ?? "—"}
        />
        <KpiCard
          icon={<Activity className="size-5" />}
          label="Active Users"
          value={data ? (data.items?.filter((u) => u.is_active).length ?? 0) : "—"}
        />
      </div>

      {/* Filter bar */}
      <div className="mt-6 flex flex-wrap items-center gap-2">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 size-3.5 text-ink-muted pointer-events-none" />
          <input
            type="text"
            placeholder="Search by email or name…"
            value={search}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full h-8 pl-8 pr-3 rounded-md border border-border bg-bg text-sm text-ink placeholder:text-ink-subtle outline-none focus:border-brand-500 transition-colors"
          />
        </div>

        <select
          value={role}
          onChange={(e) => {
            setRole(e.target.value);
            setOffset(0);
          }}
          className={selectCls}
        >
          {ROLE_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setOffset(0);
          }}
          className={selectCls}
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        {hasActiveFilter && (
          <Button variant="ghost" size="sm" onClick={clearFilters}>
            <X className="size-3.5" /> Clear
          </Button>
        )}
      </div>

      {/* Users table */}
      <Card className="mt-4">
        {isLoading ? (
          <div className="py-16">
            <Loader label="Loading users…" />
          </div>
        ) : !data || filteredUsers.length === 0 ? (
          <div className="py-16 text-center">
            <Users className="size-8 text-ink-subtle mx-auto mb-3" />
            <p className="text-sm font-medium text-ink">No users found</p>
            <p className="text-xs text-ink-muted mt-1">
              {hasActiveFilter ? "Try adjusting your filters." : "Users will appear here."}
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-bg-subtle/60 text-ink-muted border-b border-border">
                  <tr className="text-left">
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Full Name</th>
                    <th className="px-4 py-3 font-medium">Role</th>
                    <th className="px-4 py-3 font-medium">Status</th>
                    <th className="px-4 py-3 font-medium whitespace-nowrap">Joined</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredUsers.map((user) => (
                    <UserRow
                      key={user.id}
                      user={user}
                      onDeactivate={handleDeactivate}
                      onEdit={handleEdit}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-4 py-3 border-t border-border flex items-center justify-between text-sm">
              <p className="text-ink-muted">
                Showing{" "}
                <span className="font-medium text-ink">
                  {offset + 1}–{Math.min(offset + limit, data.total)}
                </span>{" "}
                of{" "}
                <span className="font-medium text-ink">{data.total.toLocaleString()}</span>{" "}
                users
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={offset === 0}
                  onClick={() => setOffset(Math.max(0, offset - limit))}
                >
                  Previous
                </Button>
                <span className="text-ink-muted text-xs">
                  {Math.floor(offset / limit) + 1} / {Math.ceil(data.total / limit)}
                </span>
                <Button
                  variant="secondary"
                  size="sm"
                  disabled={!data.has_next}
                  onClick={() => setOffset(offset + limit)}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        )}
      </Card>

      {/* Edit modal */}
      {showEditModal && editingUser && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
          <Card className="max-w-md w-full mx-4">
            <CardHeader>
              <CardTitle>Edit User: {editingUser.email}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ink mb-1">Role</label>
                <select
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className={selectCls}
                >
                  <option value="patient">Patient</option>
                  <option value="doctor">Doctor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={editForm.is_active}
                  onChange={(e) => setEditForm({ ...editForm, is_active: e.target.checked })}
                  className="h-4 w-4 rounded border-border"
                />
                <label htmlFor="is_active" className="text-sm font-medium text-ink">
                  Active
                </label>
              </div>
              <div className="flex items-center gap-2 justify-end pt-4">
                <Button
                  variant="ghost"
                  onClick={() => setShowEditModal(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSaveEdit}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Saving..." : "Save"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
