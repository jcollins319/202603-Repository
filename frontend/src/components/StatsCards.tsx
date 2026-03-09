"use client";

import { Stats } from "@/lib/api";
import { formatCurrency, formatNumber } from "@/lib/format";

interface Props {
  stats: Stats;
}

export default function StatsCards({ stats }: Props) {
  const cards = [
    {
      label: "Total Sales",
      value: formatCurrency(stats.total_sales),
      color: "text-red-400",
    },
    {
      label: "Total Purchases",
      value: formatCurrency(stats.total_purchases),
      color: "text-green-400",
    },
    {
      label: "Net Insider Flow",
      value: formatCurrency(Math.abs(stats.net_flow)),
      color: stats.net_flow >= 0 ? "text-green-400" : "text-red-400",
      prefix: stats.net_flow >= 0 ? "+" : "-",
    },
    {
      label: "Transactions",
      value: formatNumber(stats.transaction_count),
      color: "text-blue-400",
    },
    {
      label: "Companies",
      value: formatNumber(stats.unique_companies),
      color: "text-purple-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="card">
          <p className="text-xs text-gray-500 uppercase tracking-wider">{card.label}</p>
          <p className={`text-xl font-bold mt-1 ${card.color}`}>
            {card.prefix || ""}
            {card.value}
          </p>
          <p className="text-xs text-gray-600 mt-1">Last {stats.period_days} days</p>
        </div>
      ))}
    </div>
  );
}
