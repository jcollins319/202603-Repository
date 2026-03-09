# InsiderFlow

Insider stock trading intelligence dashboard. Tracks insider sales and purchases across U.S. public companies using SEC Form 4 filings.

## Architecture

- **Backend**: Python FastAPI + PostgreSQL + Redis
- **ETL**: SEC EDGAR RSS feed ingestion with XML parsing, scheduled every 5 minutes
- **Frontend**: Next.js 14 + React + Tailwind CSS + Recharts
- **Deployment**: Docker Compose

## Quick Start

```bash
# Start all services
docker compose up --build

# Access
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# API docs: http://localhost:8000/docs
```

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /api/transactions/latest` | Latest insider transactions (filterable) |
| `GET /api/transactions/stats` | Aggregate stats for dashboard |
| `GET /api/transactions/export` | Export as CSV or XLSX |
| `GET /api/company/{ticker}` | Company insider activity detail |
| `GET /api/company/{ticker}/chart-data` | Time-series chart data |
| `GET /api/company/scores` | Insider score (sell/buy ratio) |
| `GET /api/insider/{id}` | Insider profile with history |
| `GET /api/alerts` | Unusual activity alerts |
| `POST /api/ingest` | Manually trigger ingestion |
| `GET /api/health` | Health check |

## Filters

All transaction endpoints support:
- `ticker` - Filter by stock symbol
- `transaction_type` - S (Sale) or P (Purchase)
- `min_value` / `max_value` - Dollar value range
- `start_date` / `end_date` - Date range (YYYY-MM-DD)
- `sort_by` - filing_date, transaction_date, value, shares
- `sort_order` - asc, desc

## Alert Detection

The system automatically detects:
- **Cluster Selling**: 3+ insiders sell within 7 days
- **Large Sale**: Single sale > $5M
- **Ownership Reduction**: Insider sells > 10% of holdings

## Database Schema

### Tables
- `companies` - Ticker, name, CIK, sector, industry
- `insiders` - Name, title, company relationship
- `transactions` - Trade details (type, shares, price, value, ownership)
- `alerts` - Detected unusual activity

## Development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://insiderflow:insiderflow@db:5432/insiderflow` | PostgreSQL connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection |
| `SEC_USER_AGENT` | `InsiderFlow admin@insiderflow.com` | SEC API user agent (required) |
| `POLLING_INTERVAL_SECONDS` | `300` | ETL polling interval |

## Data Source

All data is sourced from [SEC EDGAR](https://www.sec.gov/edgar) Form 4 filings, which are public records of insider transactions at U.S. public companies.
