from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Company, Insider, Transaction
from app.models.schemas import InsiderDetail, TransactionListItem

router = APIRouter(prefix="/api/insider", tags=["insiders"])


@router.get("/", response_model=list[dict])
def search_insiders(
    search: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search insiders by name."""
    results = (
        db.query(Insider, Company.ticker, Company.name.label("company_name"))
        .join(Company, Insider.company_id == Company.id)
        .filter(Insider.name.ilike(f"%{search}%"))
        .order_by(Insider.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [
        {
            "id": r.Insider.id,
            "name": r.Insider.name,
            "title": r.Insider.title,
            "ticker": r.ticker,
            "company_name": r.company_name,
        }
        for r in results
    ]


@router.get("/{insider_id}", response_model=InsiderDetail)
def get_insider(insider_id: int, db: Session = Depends(get_db)):
    """Get insider detail with transaction history."""
    insider = db.query(Insider).filter(Insider.id == insider_id).first()
    if not insider:
        raise HTTPException(status_code=404, detail="Insider not found")

    company = db.query(Company).filter(Company.id == insider.company_id).first()

    sales_total = (
        db.query(func.sum(Transaction.value))
        .filter(Transaction.insider_id == insider.id, Transaction.transaction_type == "S")
        .scalar()
        or 0
    )
    purchases_total = (
        db.query(func.sum(Transaction.value))
        .filter(Transaction.insider_id == insider.id, Transaction.transaction_type == "P")
        .scalar()
        or 0
    )
    txn_count = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.insider_id == insider.id)
        .scalar()
        or 0
    )

    transactions = (
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
        .filter(Transaction.insider_id == insider.id)
        .order_by(desc(Transaction.transaction_date))
        .limit(200)
        .all()
    )

    from app.models.schemas import CompanyResponse

    return InsiderDetail(
        id=insider.id,
        name=insider.name,
        title=insider.title,
        company_id=insider.company_id,
        cik=insider.cik,
        created_at=insider.created_at,
        company=CompanyResponse.model_validate(company) if company else None,
        total_sales=sales_total,
        total_purchases=purchases_total,
        transaction_count=txn_count,
        transactions=[TransactionListItem.model_validate(r._asdict()) for r in transactions],
    )
