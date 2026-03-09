# InsiderFlow Dashboard — Usage Guide

A step-by-step guide to getting started with the InsiderFlow insider trading dashboard.

## Prerequisites

- **Docker and Docker Compose** (recommended), or
- **Python 3.11+**, **Node.js 18+**, **PostgreSQL 16**, and **Redis 7** for manual setup

## 1. Starting the Application

### Option A: Docker Compose (Recommended)

```bash
git clone <repo-url> && cd 202603-Repository
docker compose up --build
```

This launches all four services (PostgreSQL, Redis, FastAPI backend, Next.js frontend). Wait until you see log output from all containers, then open:

- **Dashboard UI**: http://localhost:3000
- **API docs (Swagger)**: http://localhost:8000/docs

### Option B: Manual Setup

Start PostgreSQL and Redis on your machine, then:

```bash
# Terminal 1 — Backend
cd backend
cp .env.example .env          # edit DATABASE_URL / REDIS_URL if needed
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload  # http://localhost:8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev                    # http://localhost:3000
```

## 2. Configuration

Copy `backend/.env.example` to `backend/.env` and adjust:

| Variable | Default | Notes |
|---|---|---|
| `SEC_USER_AGENT` | `InsiderFlow admin@insiderflow.com` | **Change this** — SEC requires a valid contact email |
| `POLLING_INTERVAL_SECONDS` | `300` | Seconds between automatic data fetches (default: 5 min) |
| `DATABASE_URL` | `postgresql://insiderflow:insiderflow@db:5432/insiderflow` | Adjust host to `localhost` for manual setup |
| `REDIS_URL` | `redis://redis:6379/0` | Adjust host to `localhost` for manual setup |

## 3. Using the Dashboard

### Main Dashboard (Home Page)

When you open `http://localhost:3000`, you'll see:

- **Stats Cards** at the top — total sales volume, total purchases, net insider flow, transaction count, and number of tracked companies.
- **Recent Alerts** — the latest automatically-detected anomalies (see Section 5).
- **Transactions Table** — a paginated list of the most recent insider trades with columns for insider name, company ticker, transaction type, shares, price, value, and filing date.
- **Filters** — narrow results by ticker, transaction type (Sale or Purchase), dollar value range, and date range.
- **Export Buttons** — download the current filtered view as CSV or XLSX.

### Company Detail Page

Click any ticker in the transactions table to navigate to `/company/[ticker]`. This page shows:

- Company-level aggregate metrics (total insider sales, purchases, and net flow).
- A **time-series chart** (Recharts) showing weekly insider activity over time.
- A filtered transaction table showing only that company's insider trades.

### Insider Profile Page

Click any insider name to navigate to `/insider/[id]`. This shows:

- The insider's name, title, and company affiliation.
- Aggregate stats (total sales, total purchases, number of transactions).
- Full transaction history for that insider.

### Alerts Page

Navigate to `/alerts` to see all detected anomalies. You can filter by:

- **Alert type**: cluster_selling, large_sale, or ownership_reduction
- **Severity**: HIGH or MEDIUM

## 4. Filtering and Searching

All transaction views support the following filters:

| Filter | Example | Description |
|---|---|---|
| Ticker | `AAPL` | Show only transactions for a specific company |
| Transaction type | `S` or `P` | Sales only or Purchases only |
| Min value | `100000` | Transactions worth at least $100K |
| Max value | `5000000` | Transactions worth at most $5M |
| Start date | `2025-01-01` | Transactions on or after this date |
| End date | `2025-12-31` | Transactions on or before this date |
| Sort by | `value` | Sort by filing_date, transaction_date, value, or shares |
| Sort order | `desc` | Ascending or descending |

## 5. Alert Detection

The ETL pipeline automatically flags unusual insider activity after every data ingestion cycle:

| Alert Type | Trigger | Severity |
|---|---|---|
| **Cluster Selling** | 3 or more insiders at the same company sell within a 7-day window | HIGH |
| **Large Sale** | A single insider sale exceeds $5,000,000 | HIGH |
| **Ownership Reduction** | An insider sells more than 10% of their holdings in one transaction | MEDIUM |

Alerts appear on the main dashboard and the dedicated `/alerts` page.

## 6. Data Ingestion

Data is pulled automatically from the SEC EDGAR RSS feed on a schedule (default: every 5 minutes). You can also trigger a manual ingestion:

```bash
curl -X POST http://localhost:8000/api/ingest
```

Or use the Swagger UI at `http://localhost:8000/docs` and click **Try it out** on the `/api/ingest` endpoint.

The ingestion pipeline:
1. Fetches recent Form 4 filings from SEC EDGAR.
2. Parses the XML to extract issuer, insider, and transaction data.
3. Deduplicates using SEC accession numbers.
4. Inserts/updates companies, insiders, and transactions.
5. Runs alert detection on newly ingested data.

## 7. Exporting Data

From the dashboard, use the **CSV** or **XLSX** export buttons. These respect your current filters, so you can export a targeted subset of transactions.

Programmatically:

```bash
# CSV export
curl "http://localhost:8000/api/transactions/export?format=csv&ticker=AAPL" -o trades.csv

# Excel export
curl "http://localhost:8000/api/transactions/export?format=xlsx&ticker=AAPL" -o trades.xlsx
```

## 8. API Reference

The API is fully documented with interactive examples at `http://localhost:8000/docs`. Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/transactions/latest` | Paginated, filterable transaction list |
| GET | `/api/transactions/stats` | Aggregate dashboard metrics |
| GET | `/api/transactions/export` | CSV/XLSX download |
| GET | `/api/company/{ticker}` | Company detail with insider summary |
| GET | `/api/company/{ticker}/chart-data` | Weekly time-series data for charts |
| GET | `/api/company/scores` | Companies ranked by insider sell/buy ratio |
| GET | `/api/insider/{id}` | Insider profile with transaction history |
| GET | `/api/insider/` | Search insiders by name |
| GET | `/api/alerts` | Alert list with type/severity filters |
| POST | `/api/ingest` | Trigger manual data ingestion |
| GET | `/api/health` | Health check |

## 9. Troubleshooting

| Problem | Solution |
|---|---|
| No transactions showing | The ETL may not have run yet. Trigger manually: `curl -X POST http://localhost:8000/api/ingest` |
| Frontend can't reach backend | Check that the backend is running on port 8000 and CORS is configured (default allows `localhost:3000`) |
| SEC rate limiting | The client is rate-limited to 10 req/s. If you see 429 errors, increase the delay in `sec_client.py` |
| Database connection errors | Verify `DATABASE_URL` in `.env` — use `localhost` for manual setup, `db` for Docker |
