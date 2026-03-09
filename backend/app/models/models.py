from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cik: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    insiders: Mapped[list["Insider"]] = relationship(back_populates="company")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="company")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="company")


class Insider(Base):
    __tablename__ = "insiders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(100))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    cik: Mapped[str | None] = mapped_column(String(20), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="insiders")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="insider")

    __table_args__ = (
        Index("ix_insiders_company_name", "company_id", "name"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    insider_id: Mapped[int] = mapped_column(ForeignKey("insiders.id"), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)  # P-Purchase, S-Sale
    shares: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    ownership_after: Mapped[int | None] = mapped_column(BigInteger)
    ownership_change_pct: Mapped[float | None] = mapped_column(Float)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    filing_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    form_type: Mapped[str] = mapped_column(String(10), default="4")
    accession_number: Mapped[str | None] = mapped_column(String(30), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="transactions")
    insider: Mapped["Insider"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_company_date", "company_id", "transaction_date"),
        Index("ix_transactions_type_date", "transaction_type", "transaction_date"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    transaction_ids: Mapped[str | None] = mapped_column(Text)  # comma-separated IDs
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    company: Mapped["Company"] = relationship(back_populates="alerts")
