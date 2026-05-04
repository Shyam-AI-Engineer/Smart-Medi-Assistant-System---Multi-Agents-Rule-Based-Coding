"use client";

import { useState } from "react";
import {
  Users, MessageSquare, Activity, Brain,
  AlertTriangle, ThumbsUp, TrendingUp, Zap,
} from "lucide-react";
import {
  AreaChart, Area,
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Loader } from "@/components/ui/Loader";
import {
  useAdminOverview,
  useAdminDailyMetrics,
  useAdminAgentStats,
  useAdminAnomalyTrend,
} from "@/hooks/useAdminAnalytics";
import { cn } from "@/lib/cn";

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmtDay(iso: string) {
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function fmtAgent(s: string) {
  const map: Record<string, string> = {
    orchestrator: "Orchestrator",
    clinical: "Clinical",
    rag: "RAG",
    triage: "Triage",
    medication: "Medication",
    monitoring: "Monitoring",
    "follow-up": "Follow-up",
    error_handler: "Fallback",
  };
  return map[s] ?? s.charAt(0).toUpperCase() + s.slice(1);
}

const PIE_COLORS = [
  "#6366f1", "#22c55e", "#f59e0b", "#ef4444",
  "#8b5cf6", "#06b6d4", "#f97316", "#84cc16",
];

const CHART_STYLE = {
  fontSize: 11,
  fill: "#6b7280",
};

// ── KPI card ──────────────────────────────────────────────────────────────────

interface KpiCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  tone?: "brand" | "success" | "warning" | "danger" | "neutral";
  loading?: boolean;
}

const TONE_CLS: Record<NonNullable<KpiCardProps["tone"]>, string> = {
  brand:   "text-brand-600 bg-brand-50",
  success: "text-success-600 bg-success-50",
  warning: "text-warning-600 bg-warning-50",
  danger:  "text-danger-600 bg-danger-50",
  neutral: "text-ink-muted bg-bg-subtle",
};

function KpiCard({ label, value, sub, icon: Icon, tone = "brand", loading }: KpiCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm font-medium text-ink-muted">{label}</CardTitle>
        <div className={cn("size-8 rounded-lg flex items-center justify-center", TONE_CLS[tone])}>
          <Icon className="size-4" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-ink">
          {loading ? <span className="text-ink-muted">—</span> : value}
        </div>
        {sub && <p className="text-xs text-ink-muted mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

// ── Range selector ────────────────────────────────────────────────────────────

function RangeSelector({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  const options = [7, 14, 30, 60, 90];
  return (
    <div className="flex gap-1 p-1 rounded-lg bg-bg-subtle border border-border w-fit">
      {options.map((d) => (
        <button
          key={d}
          onClick={() => onChange(d)}
          className={cn(
            "px-3 py-1 rounded-md text-xs font-medium transition-colors",
            value === d ? "bg-bg shadow-sm text-ink" : "text-ink-muted hover:text-ink",
          )}
        >
          {d}d
        </button>
      ))}
    </div>
  );
}

// ── Empty chart state ─────────────────────────────────────────────────────────

function ChartEmpty({ label }: { label: string }) {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-2 py-12">
      <TrendingUp className="size-8 text-ink-subtle" />
      <p className="text-sm text-ink-muted">No {label} data yet</p>
      <p className="text-xs text-ink-subtle">Data will appear once patients start using the platform.</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminDashboardPage() {
  const [days, setDays] = useState(30);

  const { data: overview, isLoading: ovLoading } = useAdminOverview();
  const { data: daily, isLoading: dailyLoading } = useAdminDailyMetrics(days);
  const { data: agents, isLoading: agentsLoading } = useAdminAgentStats(days);
  const { data: anomalies, isLoading: anomalyLoading } = useAdminAnomalyTrend(days);

  const pieData = agents?.map((a) => ({
    name: fmtAgent(a.agent),
    value: a.count,
  })) ?? [];

  const dailyFormatted = daily?.map((d) => ({
    ...d,
    day: fmtDay(d.day),
    confidence_pct: +(d.avg_confidence * 100).toFixed(1),
  })) ?? [];

  const anomalyFormatted = anomalies?.map((d) => ({
    ...d,
    day: fmtDay(d.day),
  })) ?? [];

  return (
    <div className="container py-8 max-w-7xl space-y-8">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <PageHeader
          title="Analytics Dashboard"
          description="Platform-wide metrics — usage, AI performance, and health outcomes."
        />
        <RangeSelector value={days} onChange={setDays} />
      </div>

      {/* ── KPI Cards ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <KpiCard
          label="Total Patients"
          value={overview?.total_patients ?? 0}
          sub="Registered on platform"
          icon={Users}
          tone="brand"
          loading={ovLoading}
        />
        <KpiCard
          label="Daily Active Users"
          value={overview?.dau ?? 0}
          sub="Patients active today"
          icon={Zap}
          tone="success"
          loading={ovLoading}
        />
        <KpiCard
          label="Messages Today"
          value={overview?.messages_today ?? 0}
          sub={`${overview?.total_messages ?? 0} total`}
          icon={MessageSquare}
          tone="brand"
          loading={ovLoading}
        />
        <KpiCard
          label="Avg AI Confidence"
          value={overview ? `${(overview.avg_confidence * 100).toFixed(1)}%` : "—"}
          sub="Across all responses"
          icon={Brain}
          tone={
            !overview ? "neutral"
              : overview.avg_confidence >= 0.8 ? "success"
              : overview.avg_confidence >= 0.5 ? "warning"
              : "danger"
          }
          loading={ovLoading}
        />
        <KpiCard
          label="Anomaly Detection Rate"
          value={overview ? `${overview.anomaly_rate}%` : "—"}
          sub={`${overview?.total_vitals ?? 0} vitals recorded`}
          icon={AlertTriangle}
          tone={
            !overview ? "neutral"
              : overview.anomaly_rate > 20 ? "danger"
              : overview.anomaly_rate > 10 ? "warning"
              : "success"
          }
          loading={ovLoading}
        />
        <KpiCard
          label="User Satisfaction"
          value={overview?.satisfaction_rate != null ? `${overview.satisfaction_rate}%` : "N/A"}
          sub="Thumbs-up feedback rate"
          icon={ThumbsUp}
          tone={
            overview?.satisfaction_rate == null ? "neutral"
              : overview.satisfaction_rate >= 75 ? "success"
              : overview.satisfaction_rate >= 50 ? "warning"
              : "danger"
          }
          loading={ovLoading}
        />
        <KpiCard
          label="Total AI Messages"
          value={overview?.total_messages ?? 0}
          sub="All-time conversations"
          icon={Activity}
          tone="neutral"
          loading={ovLoading}
        />
        <KpiCard
          label="Total Vitals Logged"
          value={overview?.total_vitals ?? 0}
          sub="Patient readings stored"
          icon={Activity}
          tone="neutral"
          loading={ovLoading}
        />
      </div>

      {/* ── Messages Per Day ── */}
      <Card>
        <CardHeader>
          <CardTitle>Messages Per Day</CardTitle>
        </CardHeader>
        <CardContent>
          {dailyLoading ? (
            <div className="py-12"><Loader label="Loading…" /></div>
          ) : dailyFormatted.length === 0 ? (
            <ChartEmpty label="daily messages" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={dailyFormatted} margin={{ top: 4, right: 16, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="msgGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.18} />
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="day" tick={CHART_STYLE} interval="preserveStartEnd" />
                <YAxis tick={CHART_STYLE} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                  formatter={(v: number) => [v, "Messages"]}
                />
                <Area
                  type="monotone"
                  dataKey="messages"
                  stroke="#6366f1"
                  strokeWidth={2}
                  fill="url(#msgGrad)"
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* ── Agent Distribution + Daily Active Patients ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Agent Routing Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            {agentsLoading ? (
              <div className="py-12"><Loader label="Loading…" /></div>
            ) : pieData.length === 0 ? (
              <ChartEmpty label="agent routing" />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {pieData.map((_, i) => (
                      <Cell
                        key={i}
                        fill={PIE_COLORS[i % PIE_COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                    formatter={(v: number) => [v, "Requests"]}
                  />
                  <Legend
                    iconSize={10}
                    wrapperStyle={{ fontSize: 11 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Daily Active Patients</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyLoading ? (
              <div className="py-12"><Loader label="Loading…" /></div>
            ) : dailyFormatted.length === 0 ? (
              <ChartEmpty label="active patient" />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={dailyFormatted}
                  margin={{ top: 4, right: 16, left: -20, bottom: 0 }}
                  barSize={14}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="day" tick={CHART_STYLE} interval="preserveStartEnd" />
                  <YAxis tick={CHART_STYLE} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                    formatter={(v: number) => [v, "Active patients"]}
                  />
                  <Bar
                    dataKey="active_patients"
                    fill="#22c55e"
                    radius={[3, 3, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Confidence Trend + Anomaly Rate ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Average AI Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            {dailyLoading ? (
              <div className="py-12"><Loader label="Loading…" /></div>
            ) : dailyFormatted.length === 0 ? (
              <ChartEmpty label="confidence" />
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <LineChart
                  data={dailyFormatted}
                  margin={{ top: 4, right: 16, left: -20, bottom: 0 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="day" tick={CHART_STYLE} interval="preserveStartEnd" />
                  <YAxis tick={CHART_STYLE} domain={[0, 100]} unit="%" />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                    formatter={(v: number) => [`${v}%`, "Avg confidence"]}
                  />
                  <Line
                    type="monotone"
                    dataKey="confidence_pct"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Anomaly Detection Rate</CardTitle>
          </CardHeader>
          <CardContent>
            {anomalyLoading ? (
              <div className="py-12"><Loader label="Loading…" /></div>
            ) : anomalyFormatted.length === 0 ? (
              <ChartEmpty label="anomaly" />
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart
                  data={anomalyFormatted}
                  margin={{ top: 4, right: 16, left: -20, bottom: 0 }}
                >
                  <defs>
                    <linearGradient id="anomalyGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ef4444" stopOpacity={0.18} />
                      <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="day" tick={CHART_STYLE} interval="preserveStartEnd" />
                  <YAxis tick={CHART_STYLE} unit="%" domain={[0, "auto"]} />
                  <Tooltip
                    contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
                    formatter={(v: number) => [`${v}%`, "Anomaly rate"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="rate"
                    stroke="#ef4444"
                    strokeWidth={2}
                    fill="url(#anomalyGrad)"
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
