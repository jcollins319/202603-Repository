"use client";

import { Suspense, useEffect, useState } from "react";
import { api, Stats, Transaction, Alert } from "@/lib/api";
import StatsCards from "@/components/StatsCards";
import TransactionTable from "@/components/TransactionTable";
import AlertList from "@/components/AlertList";
import Filters from "@/components/Filters";

function DashboardContent() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [s, t, a] = await Promise.all([
          api.getStats(7),
          api.getLatestTransactions({ page_size: "50", sort_by: "filing_date", sort_order: "desc" }),
          api.getAlerts({ page_size: "5" }),
        ]);
        setStats(s);
        setTransactions(t);
        setAlerts(a);
      } catch (e) {
        console.error("Failed to load dashboard data:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="text-gray-500 text-center py-12">Loading dashboard...</div>;
  }

  return (
    <div className="space-y-6">
      {stats && <StatsCards stats={stats} />}

      {alerts.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Recent Alerts</h2>
          <AlertList alerts={alerts} />
        </section>
      )}

      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Latest Insider Transactions</h2>
          <div className="flex gap-2">
            <a
              href={api.getExportUrl("csv")}
              className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded transition-colors"
            >
              Export CSV
            </a>
            <a
              href={api.getExportUrl("xlsx")}
              className="text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded transition-colors"
            >
              Export XLSX
            </a>
          </div>
        </div>
        <Filters />
        <div className="mt-4">
          <TransactionTable transactions={transactions} />
        </div>
      </section>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={<div className="text-gray-500 text-center py-12">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  );
}
