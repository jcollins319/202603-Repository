"use client";

import Link from "next/link";
import { Alert } from "@/lib/api";
import { formatDate } from "@/lib/format";

interface Props {
  alerts: Alert[];
}

const alertTypeLabels: Record<string, string> = {
  cluster_selling: "Cluster Selling",
  large_sale: "Large Sale",
  ownership_reduction: "Ownership Reduction",
  new_seller: "New Seller",
};

export default function AlertList({ alerts }: Props) {
  if (alerts.length === 0) {
    return <p className="text-gray-500 text-center py-8">No alerts found.</p>;
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div key={alert.id} className="card flex items-start gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={`badge-alert-${alert.severity}`}>
                {alert.severity.toUpperCase()}
              </span>
              <span className="text-xs text-gray-500">
                {alertTypeLabels[alert.alert_type] || alert.alert_type}
              </span>
            </div>
            <p className="text-sm text-gray-200">{alert.description}</p>
            {alert.company && (
              <Link
                href={`/company/${alert.company.ticker}`}
                className="text-xs text-blue-400 hover:text-blue-300 mt-1 inline-block"
              >
                {alert.company.ticker} - {alert.company.name}
              </Link>
            )}
          </div>
          <span className="text-xs text-gray-500 whitespace-nowrap">
            {formatDate(alert.created_at)}
          </span>
        </div>
      ))}
    </div>
  );
}
