from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Company, Insider, Transaction
from app.models.schemas import CompanyDetail, CompanyResponse, InsiderScore, TransactionListItem

router = APIRouter(prefix="/api/company", tags=["companies"])


@router.get("/", response_model=list[CompanyResponse])
def list_companies(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List companies with optional search."""
    query = db.query(Company)
    if search:
        query = query.filter(
            Company.ticker.ilike(f"%{search}%") | Company.name.ilike(f"%{search}%")
        )
    results = query.order_by(Company.ticker).offset((page - 1) * page_size).limit(page_size).all()
    return results


@router.get("/scores", response_model=list[InsiderScore])
def get_insider_scores(
    days: int = Query(90, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get insider score (sell/buy ratio) for companies."""
    from sqlalchemy import case, text

    interval = text(f"INTERVAL '{days} days'")

    results = (
        db.query(
            Company.ticker,
            Company.name.label("company_name"),
            func.sum(
                case((Transaction.transaction_type == "S", Transaction.value), else_=0)
            ).label("selling_total"),
            func.sum(
                case((Transaction.transaction_type == "P", Transaction.value), else_=0)
            ).label("buying_total"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Transaction, Transaction.company_id == Company.id)
        .filter(Transaction.transaction_date >= func.now() - interval)
        .group_by(Company.id, Company.ticker, Company.name)
        .having(func.count(Transaction.id) > 0)
        .order_by(
            desc(
                func.sum(
                    case((Transaction.transaction_type == "S", Transaction.value), else_=0)
                )
                / func.nullif(
                    func.sum(
                        case((Transaction.transaction_type == "P", Transaction.value), else_=0)
                    ),
                    0,
                )
            )
        )
        .limit(limit)
        .all()
    )

    scores = []
    for r in results:
        buying = r.buying_total or 0
        selling = r.selling_total or 0
        score = (selling / buying) if buying > 0 else (selling if selling > 0 else 0)
        scores.append(
            InsiderScore(
                ticker=r.ticker,
                company_name=r.company_name,
                selling_total=selling,
                buying_total=buying,
                score=round(score, 2),
                transaction_count=r.transaction_count,
            )
        )
    return scores


@router.get("/{ticker}", response_model=CompanyDetail)
def get_company(ticker: str, db: Session = Depends(get_db)):
    """Get company detail with insider activity summary."""
    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Aggregate stats
    sales_total = (
        db.query(func.sum(Transaction.value))
        .filter(Transaction.company_id == company.id, Transaction.transaction_type == "S")
        .scalar()
        or 0
    )
    purchases_total = (
        db.query(func.sum(Transaction.value))
        .filter(Transaction.company_id == company.id, Transaction.transaction_type == "P")
        .scalar()
        or 0
    )
    txn_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.company_id == company.id)
        .scalar()
        or 0
    )

    # Recent transactions
    recent = (
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
        .filter(Transaction.company_id == company.id)
        .order_by(desc(Transaction.transaction_date))
        .limit(100)
        .all()
    )

    return CompanyDetail(
        id=company.id,
        ticker=company.ticker,
        name=company.name,
        cik=company.cik,
        sector=company.sector,
        industry=company.industry,
        created_at=company.created_at,
        total_insider_sales=sales_total,
        total_insider_purchases=purchases_total,
        net_insider_flow=purchases_total - sales_total,
        transaction_count=txn_count,
        recent_transactions=[TransactionListItem.model_validate(r._asdict()) for r in recent],
    )


@router.get("/{ticker}/chart-data")
def get_company_chart_data(
    ticker: str,
    days: int = Query(365, ge=1, le=1825),
    db: Session = Depends(get_db),
):
    """Get time-series insider activity data for charting."""
    from sqlalchemy import case, text

    company = db.query(Company).filter(Company.ticker == ticker.upper()).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    interval = text(f"INTERVAL '{days} days'")

    results = (
        db.query(
            func.date_trunc("week", Transaction.transaction_date).label("week"),
            func.sum(
                case((Transaction.transaction_type == "S", Transaction.value), else_=0)
            ).label("selling"),
            func.sum(
                case((Transaction.transaction_type == "P", Transaction.value), else_=0)
            ).label("buying"),
        )
        .filter(
            Transaction.company_id == company.id,
            Transaction.transaction_date >= func.now() - interval,
        )
        .group_by(func.date_trunc("week", Transaction.transaction_date))
        .order_by(func.date_trunc("week", Transaction.transaction_date))
        .all()
    )

    return [
        {
            "week": str(r.week.date()) if r.week else None,
            "selling": float(r.selling or 0),
            "buying": float(r.buying or 0),
            "net_flow": float((r.buying or 0) - (r.selling or 0)),
        }
        for r in results
    ]
