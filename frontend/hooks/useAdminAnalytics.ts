"use client";

import { useQuery } from "@tanstack/react-query";
import { endpoints } from "@/lib/api";

export function useAdminOverview() {
  return useQuery({
    queryKey: ["admin-overview"],
    queryFn: () => endpoints.adminOverview(),
    refetchInterval: 60_000,
  });
}

export function useAdminDailyMetrics(days = 30) {
  return useQuery({
    queryKey: ["admin-daily", days],
    queryFn: () => endpoints.adminDailyMetrics(days),
  });
}

export function useAdminAgentStats(days = 30) {
  return useQuery({
    queryKey: ["admin-agents", days],
    queryFn: () => endpoints.adminAgentStats(days),
  });
}

export function useAdminAnomalyTrend(days = 30) {
  return useQuery({
    queryKey: ["admin-anomalies", days],
    queryFn: () => endpoints.adminAnomalyTrend(days),
  });
}

export function useAuditLogs(params: Parameters<typeof endpoints.auditLogs>[0]) {
  return useQuery({
    queryKey: ["admin-audit-logs", params],
    queryFn: () => endpoints.auditLogs(params),
    placeholderData: (prev) => prev,
  });
}

export function useAuditLogsSummary(days = 30) {
  return useQuery({
    queryKey: ["admin-audit-summary", days],
    queryFn: () => endpoints.auditLogsSummary(days),
  });
}

export function useAdminUsers(limit = 50, offset = 0, search = "", role = "") {
  return useQuery({
    queryKey: ["admin-users", limit, offset, search, role],
    queryFn: () => endpoints.listAdminUsers({ limit, offset, search, role }),
    placeholderData: (prev) => prev,
  });
}
