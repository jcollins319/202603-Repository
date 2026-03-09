"use client";

import Link from "next/link";
import { Transaction } from "@/lib/api";
import { formatCurrency, formatDate, formatNumber, formatPercent } from "@/lib/format";

interface Props {
  transactions: Transaction[];
  showCompany?: boolean;
}

export default function TransactionTable({ transactions, showCompany = true }: Props) {
  if (transactions.length === 0) {
    return <p className="text-gray-500 text-center py-8">No transactions found.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-800">
            {showCompany && <th className="pb-3 pr-4">Ticker</th>}
            {showCompany && <th className="pb-3 pr-4">Company</th>}
            <th className="pb-3 pr-4">Insider</th>
            <th className="pb-3 pr-4">Title</th>
            <th className="pb-3 pr-4">Type</th>
            <th className="pb-3 pr-4 text-right">Shares</th>
            <th className="pb-3 pr-4 text-right">Price</th>
            <th className="pb-3 pr-4 text-right">Value</th>
            <th className="pb-3 pr-4 text-right">% Change</th>
            <th className="pb-3 text-right">Date</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn) => (
            <tr key={txn.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
              {showCompany && (
                <td className="py-3 pr-4">
                  <Link
                    href={`/company/${txn.ticker}`}
                    className="font-medium text-blue-400 hover:text-blue-300"
                  >
                    {txn.ticker}
                  </Link>
                </td>
              )}
              {showCompany && (
                <td className="py-3 pr-4 text-gray-300 max-w-[200px] truncate">
                  {txn.company_name}
                </td>
              )}
              <td className="py-3 pr-4 text-gray-300">{txn.insider_name}</td>
              <td className="py-3 pr-4 text-gray-500">{txn.insider_title || "-"}</td>
              <td className="py-3 pr-4">
                <span className={txn.transaction_type === "S" ? "badge-sale" : "badge-purchase"}>
                  {txn.transaction_type === "S" ? "Sale" : "Purchase"}
                </span>
              </td>
              <td className="py-3 pr-4 text-right font-mono">{formatNumber(txn.shares)}</td>
              <td className="py-3 pr-4 text-right font-mono">${txn.price.toFixed(2)}</td>
              <td className="py-3 pr-4 text-right font-mono font-medium">
                <span className={txn.transaction_type === "S" ? "text-red-400" : "text-green-400"}>
                  {formatCurrency(txn.value)}
                </span>
              </td>
              <td className="py-3 pr-4 text-right font-mono text-gray-400">
                {formatPercent(txn.ownership_change_pct)}
              </td>
              <td className="py-3 text-right text-gray-400">{formatDate(txn.transaction_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
