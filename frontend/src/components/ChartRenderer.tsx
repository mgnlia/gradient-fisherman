"use client";

import {
  BarChart, Bar,
  LineChart, Line,
  AreaChart, Area,
  ScatterChart, Scatter,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from "recharts";
import type { ChartConfig } from "@/lib/api";

const COLORS = [
  "#0ea5e9", "#6366f1", "#10b981", "#f59e0b",
  "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6",
];

interface Props {
  chart: ChartConfig;
}

export default function ChartRenderer({ chart }: Props) {
  if (!chart.show_chart || !chart.data.length) return null;

  const { chart_type, data, x_key, y_keys } = chart;

  const commonProps = {
    data,
    margin: { top: 10, right: 20, left: 0, bottom: 40 },
  };

  const xAxis = x_key ? (
    <XAxis
      dataKey={x_key}
      tick={{ fontSize: 11, fill: "#64748b" }}
      angle={-35}
      textAnchor="end"
      interval="preserveStartEnd"
    />
  ) : null;

  const yAxis = <YAxis tick={{ fontSize: 11, fill: "#64748b" }} width={60} />;
  const grid  = <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />;
  const tip   = <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />;
  const leg   = <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />;

  if (chart_type === "bar") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <BarChart {...commonProps}>
          {grid}{xAxis}{yAxis}{tip}{leg}
          {y_keys.map((k, i) => (
            <Bar key={k} dataKey={k} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "line") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart {...commonProps}>
          {grid}{xAxis}{yAxis}{tip}{leg}
          {y_keys.map((k, i) => (
            <Line
              key={k}
              type="monotone"
              dataKey={k}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={data.length <= 30}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "area") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <AreaChart {...commonProps}>
          {grid}{xAxis}{yAxis}{tip}{leg}
          {y_keys.map((k, i) => (
            <Area
              key={k}
              type="monotone"
              dataKey={k}
              stroke={COLORS[i % COLORS.length]}
              fill={COLORS[i % COLORS.length] + "33"}
              strokeWidth={2}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "scatter" && y_keys.length >= 1) {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <ScatterChart {...commonProps}>
          {grid}
          <XAxis dataKey={x_key ?? undefined} name={x_key ?? ""} tick={{ fontSize: 11 }} />
          <YAxis dataKey={y_keys[0]} name={y_keys[0]} tick={{ fontSize: 11 }} width={60} />
          {tip}
          <Scatter data={data} fill={COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  if (chart_type === "pie" && y_keys.length >= 1) {
    const pieData = data.map((row) => ({
      name: String(row[x_key ?? ""] ?? ""),
      value: Number(row[y_keys[0]] ?? 0),
    }));
    return (
      <ResponsiveContainer width="100%" height={320}>
        <PieChart>
          <Pie
            data={pieData}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            outerRadius={120}
            label={({ name, percent }) =>
              `${name} (${(percent * 100).toFixed(0)}%)`
            }
            labelLine
          >
            {pieData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          {tip}
        </PieChart>
      </ResponsiveContainer>
    );
  }

  return null;
}
