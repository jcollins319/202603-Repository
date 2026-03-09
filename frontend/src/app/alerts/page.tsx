"use client";

import { useEffect, useState } from "react";
import { api, Alert } from "@/lib/api";
import AlertList from "@/components/AlertList";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const params: Record<string, string> = { page_size: "100" };
        if (filter) params.alert_type = filter;
        const data = await api.getAlerts(params);
        setAlerts(data);
      } catch (e) {
        console.error("Failed to load alerts:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Alerts</h1>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
        >
          <option value="">All Types</option>
          <option value="cluster_selling">Cluster Selling</option>
          <option value="large_sale">Large Sale</option>
          <option value="ownership_reduction">Ownership Reduction</option>
          <option value="new_seller">New Seller</option>
        </select>
      </div>

      {loading ? (
        <div className="text-gray-500 text-center py-12">Loading alerts...</div>
      ) : (
        <AlertList alerts={alerts} />
      )}
    </div>
  );
}
