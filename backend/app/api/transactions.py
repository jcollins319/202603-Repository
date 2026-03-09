import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Company, Insider, Transaction
from app.models.schemas import TransactionListItem

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


def _build_transaction_list_query(db: Session):
    """Build the base query for transaction list items."""
    return (
        db.query(
            Transaction.id,
            Company.ticker,
            Company.name.label("company_name"),
            Insider.name.label("insider_name"),
            Insider.title.label("insider_title"),
            Transaction.transaction_type,
            Transaction.shares,
            Transaction.price,
            Transaction.value,
            Transaction.ownership_after,
            Transaction.ownership_change_pct,
            Transaction.transaction_date,
            Transaction.filing_date,
        )
        .join(Company, Transaction.company_id == Company.id)
        .join(Insider, Transaction.insider_id == Insider.id)
    )


@router.get("/latest", response_model=list[TransactionListItem])
def get_latest_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    transaction_type: str | None = None,
    ticker: str | None = None,
    insider_title: str | None = None,
    min_value: float | None = None,
    max_value: float | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    sort_by: str = Query("filing_date", pattern="^(filing_date|transaction_date|value|shares)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """Get latest insider transactions with filtering and sorting."""
    query = _build_transaction_list_query(db)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type.upper())
    if ticker:
        query = query.filter(Company.ticker == ticker.upper())
    if insider_title:
        query = query.filter(Insider.title.ilike(f"%{insider_title}%"))
    if min_value is not None:
        query = query.filter(Transaction.value >= min_value)
    if max_value is not None:
        query = query.filter(Transaction.value <= max_value)
    if start_date:
        query = query.filter(Transaction.transaction_date >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Transaction.transaction_date <= datetime.strptime(end_date, "%Y-%m-%d"))

    # Sorting
    sort_column = {
        "filing_date": Transaction.filing_date,
        "transaction_date": Transaction.transaction_date,
        "value": Transaction.value,
        "shares": Transaction.shares,
    }[sort_by]

    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)

    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()

    return [TransactionListItem.model_validate(r._asdict()) for r in results]


@router.get("/export")
def export_transactions(
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    transaction_type: str | None = None,
    ticker: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
):
    """Export transactions as CSV or XLSX."""
    query = _build_transaction_list_query(db)

    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type.upper())
    if ticker:
        query = query.filter(Company.ticker == ticker.upper())
    if start_date:
        query = query.filter(Transaction.transaction_date >= datetime.strptime(start_date, "%Y-%m-%d"))
    if end_date:
        query = query.filter(Transaction.transaction_date <= datetime.strptime(end_date, "%Y-%m-%d"))

    query = query.order_by(desc(Transaction.filing_date))
    results = query.limit(10000).all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Ticker", "Company", "Insider", "Title", "Type", "Shares",
            "Price", "Value", "Ownership After", "% Change",
            "Transaction Date", "Filing Date",
        ])
        for r in results:
            row = r._asdict()
            writer.writerow([
                row["ticker"], row["company_name"], row["insider_name"],
                row["insider_title"], row["transaction_type"], row["shares"],
                row["price"], row["value"], row["ownership_after"],
                row["ownership_change_pct"], row["transaction_date"],
                row["filing_date"],
            ])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=insider_transactions.csv"},
        )

    # XLSX export
    import openpyxl

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Insider Transactions"
    headers = [
        "Ticker", "Company", "Insider", "Title", "Type", "Shares",
        "Price", "Value", "Ownership After", "% Change",
        "Transaction Date", "Filing Date",
    ]
    ws.append(headers)
    for r in results:
        row = r._asdict()
        ws.append([
            row["ticker"], row["company_name"], row["insider_name"],
            row["insider_title"], row["transaction_type"], row["shares"],
            row["price"], row["value"], row["ownership_after"],
            row["ownership_change_pct"],
            str(row["transaction_date"]) if row["transaction_date"] else "",
            str(row["filing_date"]) if row["filing_date"] else "",
        ])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=insider_transactions.xlsx"},
    )


@router.get("/stats")
def get_transaction_stats(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get aggregate transaction stats for the dashboard."""
    from sqlalchemy import text

    interval = text(f"INTERVAL '{days} days'")

    total_sales = (
        db.query(func.sum(Transaction.value))
        .filter(
            Transaction.transaction_type == "S",
            Transaction.transaction_date >= func.now() - interval,
        )
        .scalar()
        or 0
    )

    total_purchases = (
        db.query(func.sum(Transaction.value))
        .filter(
            Transaction.transaction_type == "P",
            Transaction.transaction_date >= func.now() - interval,
        )
        .scalar()
        or 0
    )

    transaction_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.transaction_date >= func.now() - interval)
        .scalar()
        or 0
    )

    unique_companies = (
        db.query(func.count(func.distinct(Transaction.company_id)))
        .filter(Transaction.transaction_date >= func.now() - interval)
        .scalar()
        or 0
    )

    return {
        "total_sales": total_sales,
        "total_purchases": total_purchases,
        "net_flow": total_purchases - total_sales,
        "transaction_count": transaction_count,
        "unique_companies": unique_companies,
        "period_days": days,
    }
