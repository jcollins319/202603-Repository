"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, CompanyDetail, ChartDataPoint } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import TransactionTable from "@/components/TransactionTable";
import InsiderChart from "@/components/InsiderChart";

export default function CompanyPage() {
  const params = useParams();
  const ticker = (params.ticker as string).toUpperCase();
  const [company, setCompany] = useState<CompanyDetail | null>(null);
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [c, chart] = await Promise.all([
          api.getCompany(ticker),
          api.getCompanyChartData(ticker),
        ]);
        setCompany(c);
        setChartData(chart);
      } catch (e) {
        console.error("Failed to load company:", e);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [ticker]);

  if (loading) return <div className="text-gray-500 text-center py-12">Loading...</div>;
  if (!company) return <div className="text-gray-500 text-center py-12">Company not found.</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">
          {company.ticker} - {company.name}
        </h1>
        {company.sector && (
          <p className="text-sm text-gray-500 mt-1">
            {company.sector} {company.industry ? `/ ${company.industry}` : ""}
          </p>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Total Sales</p>
          <p className="text-xl font-bold text-red-400 mt-1">
            {formatCurrency(company.total_insider_sales)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Total Purchases</p>
          <p className="text-xl font-bold text-green-400 mt-1">
            {formatCurrency(company.total_insider_purchases)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Net Insider Flow</p>
          <p
            className={`text-xl font-bold mt-1 ${
              company.net_insider_flow >= 0 ? "text-green-400" : "text-red-400"
            }`}
          >
            {company.net_insider_flow >= 0 ? "+" : ""}
            {formatCurrency(company.net_insider_flow)}
          </p>
        </div>
        <div className="card">
          <p className="text-xs text-gray-500 uppercase">Transactions</p>
          <p className="text-xl font-bold text-blue-400 mt-1">{company.transaction_count}</p>
        </div>
      </div>

      <InsiderChart data={chartData} title="Insider Activity Over Time" />

      <section>
        <h2 className="text-lg font-semibold mb-3">Transaction History</h2>
        <TransactionTable transactions={company.recent_transactions} showCompany={false} />
      </section>
    </div>
  );
}
