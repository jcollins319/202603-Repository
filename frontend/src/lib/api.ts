const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface Transaction {
  id: number;
  ticker: string;
  company_name: string;
  insider_name: string;
  insider_title: string | null;
  transaction_type: string;
  shares: number;
  price: number;
  value: number;
  ownership_after: number | null;
  ownership_change_pct: number | null;
  transaction_date: string;
  filing_date: string;
}

export interface Alert {
  id: number;
  company_id: number;
  alert_type: string;
  description: string;
  severity: string;
  created_at: string;
  company: { ticker: string; name: string } | null;
}

export interface CompanyDetail {
  id: number;
  ticker: string;
  name: string;
  cik: string;
  sector: string | null;
  industry: string | null;
  total_insider_sales: number;
  total_insider_purchases: number;
  net_insider_flow: number;
  transaction_count: number;
  recent_transactions: Transaction[];
}

export interface InsiderDetail {
  id: number;
  name: string;
  title: string | null;
  company_id: number;
  total_sales: number;
  total_purchases: number;
  transaction_count: number;
  company: { ticker: string; name: string } | null;
  transactions: Transaction[];
}

export interface ChartDataPoint {
  week: string;
  selling: number;
  buying: number;
  net_flow: number;
}

export interface Stats {
  total_sales: number;
  total_purchases: number;
  net_flow: number;
  transaction_count: number;
  unique_companies: number;
  period_days: number;
}

export interface InsiderScore {
  ticker: string;
  company_name: string;
  selling_total: number;
  buying_total: number;
  score: number;
  transaction_count: number;
}

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getLatestTransactions(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return fetchJson<Transaction[]>(`${API_BASE}/transactions/latest${qs}`);
  },

  getStats(days = 7) {
    return fetchJson<Stats>(`${API_BASE}/transactions/stats?days=${days}`);
  },

  getCompany(ticker: string) {
    return fetchJson<CompanyDetail>(`${API_BASE}/company/${ticker}`);
  },

  getCompanyChartData(ticker: string, days = 365) {
    return fetchJson<ChartDataPoint[]>(
      `${API_BASE}/company/${ticker}/chart-data?days=${days}`
    );
  },

  getInsider(id: number) {
    return fetchJson<InsiderDetail>(`${API_BASE}/insider/${id}`);
  },

  getAlerts(params?: Record<string, string>) {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return fetchJson<Alert[]>(`${API_BASE}/alerts${qs}`);
  },

  getInsiderScores(days = 90) {
    return fetchJson<InsiderScore[]>(
      `${API_BASE}/company/scores?days=${days}`
    );
  },

  getExportUrl(format: "csv" | "xlsx", params?: Record<string, string>) {
    const qs = params
      ? "&" + new URLSearchParams(params).toString()
      : "";
    return `${API_BASE}/transactions/export?format=${format}${qs}`;
  },
};
