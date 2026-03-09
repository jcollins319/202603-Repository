"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, InsiderDetail } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import TransactionTable from "@/components/TransactionTable";

export default function InsiderPage() {
  const params = useParams();
  const id = Number(params.id);
  const [insider, setInsider] = useState<InsiderDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getInsider(id);
        setInsider(data);
      } catch (e) {
        console.error("Failed to load insider:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [id]);

  if (loading) return <div className="text-gray-500 text-center py-12">Loading...</div>;
  if (!insider) return <div className="text-gray-500 text-center py-12">Insider not found.</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">{insider.name}</h1>
        <p className="text-sm text-gray-500 mt-1">
          {insider.title || "Insider"}{" "}
          {insider.company && (
            <>
              at{" "}
              <Link
                href={`/company/${insider.company.ticker}`}
                className="text-blue-400 hover:text-blue-300"
              >
                {insider.company.ticker} - {insider.company.name}
              </Link>
            </>
          )}
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Total Sales</p>
          <p className="text-xl font-bold text-red-400 mt-1">
            {formatCurrency(insider.total_sales)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Total Purchases</p>
          <p className="text-xl font-bold text-green-400 mt-1">
            {formatCurrency(insider.total_purchases)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Total Transactions</p>
          <p className="text-xl font-bold text-blue-400 mt-1">{insider.transaction_count}</p>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">Transaction History</h2>
        <TransactionTable transactions={insider.transactions} />
      </section>
    </div>
  );
}
