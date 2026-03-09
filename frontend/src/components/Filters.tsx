"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";

export default function Filters() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [ticker, setTicker] = useState(searchParams.get("ticker") || "");
  const [type, setType] = useState(searchParams.get("transaction_type") || "");
  const [minValue, setMinValue] = useState(searchParams.get("min_value") || "");
  const [startDate, setStartDate] = useState(searchParams.get("start_date") || "");
  const [endDate, setEndDate] = useState(searchParams.get("end_date") || "");

  const applyFilters = useCallback(() => {
    const params = new URLSearchParams();
    if (ticker) params.set("ticker", ticker.toUpperCase());
    if (type) params.set("transaction_type", type);
    if (minValue) params.set("min_value", minValue);
    if (startDate) params.set("start_date", startDate);
    if (endDate) params.set("end_date", endDate);
    router.push(`/?${params.toString()}`);
  }, [ticker, type, minValue, startDate, endDate, router]);

  const clearFilters = useCallback(() => {
    setTicker("");
    setType("");
    setMinValue("");
    setStartDate("");
    setEndDate("");
    router.push("/");
  }, [router]);

  return (
    <div className="card">
      <div className="flex flex-wrap gap-3 items-end">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Ticker</label>
          <input
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value)}
            placeholder="AAPL"
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-24 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Type</label>
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
          >
            <option value="">All</option>
            <option value="S">Sales</option>
            <option value="P">Purchases</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Min Value ($)</label>
          <input
            type="number"
            value={minValue}
            onChange={(e) => setMinValue(e.target.value)}
            placeholder="0"
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm w-28 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
          />
        </div>
        <button
          onClick={applyFilters}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded text-sm transition-colors"
        >
          Apply
        </button>
        <button
          onClick={clearFilters}
          className="bg-gray-700 hover:bg-gray-600 text-gray-300 px-4 py-1.5 rounded text-sm transition-colors"
        >
          Clear
        </button>
      </div>
    </div>
  );
}
