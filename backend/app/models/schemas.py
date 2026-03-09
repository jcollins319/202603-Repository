from datetime import datetime

from pydantic import BaseModel


class CompanyBase(BaseModel):
    ticker: str
    name: str
    cik: str
    sector: str | None = None
    industry: str | None = None


class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InsiderBase(BaseModel):
    name: str
    title: str | None = None
    company_id: int
    cik: str | None = None


class InsiderResponse(InsiderBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionBase(BaseModel):
    transaction_type: str
    shares: int
    price: float
    value: float
    ownership_after: int | None = None
    ownership_change_pct: float | None = None
    transaction_date: datetime
    filing_date: datetime
    form_type: str = "4"


class TransactionResponse(TransactionBase):
    id: int
    company_id: int
    insider_id: int
    accession_number: str | None = None
    created_at: datetime
    company: CompanyResponse | None = None
    insider: InsiderResponse | None = None

    model_config = {"from_attributes": True}


class TransactionListItem(BaseModel):
    id: int
    ticker: str
    company_name: str
    insider_name: str
    insider_title: str | None
    transaction_type: str
    shares: int
    price: float
    value: float
    ownership_after: int | None
    ownership_change_pct: float | None
    transaction_date: datetime
    filing_date: datetime

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: int
    company_id: int
    alert_type: str
    description: str
    severity: str
    created_at: datetime
    company: CompanyResponse | None = None

    model_config = {"from_attributes": True}


class CompanyDetail(CompanyResponse):
    total_insider_sales: float = 0
    total_insider_purchases: float = 0
    net_insider_flow: float = 0
    transaction_count: int = 0
    recent_transactions: list[TransactionListItem] = []


class InsiderDetail(InsiderResponse):
    company: CompanyResponse | None = None
    total_sales: float = 0
    total_purchases: float = 0
    transaction_count: int = 0
    transactions: list[TransactionListItem] = []


class InsiderScore(BaseModel):
    ticker: str
    company_name: str
    selling_total: float
    buying_total: float
    score: float
    transaction_count: int


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int
    pages: int
