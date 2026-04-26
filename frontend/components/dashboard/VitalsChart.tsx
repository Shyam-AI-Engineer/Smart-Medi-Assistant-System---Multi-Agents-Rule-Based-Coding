"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceArea,
} from "recharts";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";

export interface ChartPoint {
  time: string;
  value: number | null;
}

interface VitalsChartProps {
  title: string;
  description?: string;
  data: ChartPoint[];
  unit?: string;
  color?: string;
  normalRange?: { min: number; max: number };
  height?: number;
}

export function VitalsChart({
  title,
  description,
  data,
  unit,
  color = "#1E86EE",
  normalRange,
  height = 240,
}: VitalsChartProps) {
  const cleanData = data.filter((d) => d.value !== null);
  const empty = cleanData.length === 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        {empty ? (
          <div className="h-[240px] flex items-center justify-center text-sm text-ink-subtle">
            No data yet — record vitals to see trends.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={color} stopOpacity={0.18} />
                  <stop offset="100%" stopColor={color} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey="time"
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                stroke="#94A3B8"
                fontSize={11}
                tickLine={false}
                axisLine={false}
                width={36}
              />
              {normalRange && (
                <ReferenceArea
                  y1={normalRange.min}
                  y2={normalRange.max}
                  fill="#10B981"
                  fillOpacity={0.06}
                  stroke="none"
                />
              )}
              <Tooltip
                contentStyle={{
                  background: "#FFFFFF",
                  border: "1px solid #E2E8F0",
                  borderRadius: "10px",
                  boxShadow: "0 4px 12px rgba(15, 23, 42, 0.06)",
                  fontSize: "12px",
                }}
                labelStyle={{ color: "#475569", fontWeight: 500 }}
                formatter={(v: number) => [`${v}${unit ? ` ${unit}` : ""}`, title]}
              />
              <Line
                type="monotone"
                dataKey="value"
                stroke={color}
                strokeWidth={2}
                dot={{ r: 0 }}
                activeDot={{ r: 4, strokeWidth: 0 }}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
