"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from "recharts";
import { ChartDataPoint } from "@/lib/api";
import { formatCurrency } from "@/lib/format";

interface Props {
  data: ChartDataPoint[];
  title?: string;
}

export default function InsiderChart({ data, title }: Props) {
  if (data.length === 0) {
    return <p className="text-gray-500 text-center py-8">No chart data available.</p>;
  }

  return (
    <div className="card">
      {title && <h3 className="text-lg font-semibold mb-4">{title}</h3>}
      <ResponsiveContainer width="100%" height={350}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="week" stroke="#6b7280" fontSize={12} />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickFormatter={(v: number) => formatCurrency(v)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "1px solid #374151",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(value: number, name: string) => [
              formatCurrency(value),
              name === "selling" ? "Insider Selling" : name === "buying" ? "Insider Buying" : "Net Flow",
            ]}
          />
          <Legend />
          <ReferenceLine y={0} stroke="#4b5563" />
          <Bar dataKey="selling" fill="#ef4444" name="Selling" />
          <Bar dataKey="buying" fill="#22c55e" name="Buying" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
